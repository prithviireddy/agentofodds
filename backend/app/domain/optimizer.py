"""Long-only minimum-variance optimiser with explicit cash and diagnostics."""
from dataclasses import dataclass
from decimal import Decimal
import numpy as np
from backend.app.domain.policy import InvestmentPolicy, PolicyError

VERSION = "projected_gradient_v2_exact_output"


@dataclass(frozen=True)
class PortfolioResult:
    status: str
    weights: dict[str, Decimal]
    cash_weight: Decimal | None
    estimated_variance: float | None
    diagnostics: dict


def _project_box_simplex(vector, lower, upper, total):
    if total < lower.sum() - 1e-12 or total > upper.sum() + 1e-12:
        raise ValueError("Box-simplex constraints are infeasible")
    low, high = float(np.min(vector - upper)) - 1.0, float(np.max(vector - lower)) + 1.0
    for _ in range(100):
        midpoint = (low + high) / 2
        projected = np.clip(vector - midpoint, lower, upper)
        if projected.sum() > total:
            low = midpoint
        else:
            high = midpoint
    return np.clip(vector - (low + high) / 2, lower, upper)


def _validated_covariance(covariance, count):
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (count, count) or not np.isfinite(matrix).all():
        raise ValueError("Covariance shape or values are invalid")
    if not np.allclose(matrix, matrix.T, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if eigenvalues.min() < -1e-10:
        raise ValueError("Covariance is not positive semidefinite")
    return matrix, eigenvalues


def solve_minimum_variance(policy: InvestmentPolicy, covariance, tolerance=1e-12, max_iterations=20_000) -> PortfolioResult:
    """Minimise w'Σw; cash is zero variance and uses its allowed maximum."""
    try:
        policy.validate()
    except PolicyError as exc:
        return PortfolioResult("infeasible", {}, None, None, {"reason": str(exc)})
    count = len(policy.symbols)
    try:
        matrix, eigenvalues = _validated_covariance(covariance, count)
        lower = np.full(count, float(policy.min_asset_weight))
        upper = np.full(count, float(policy.max_asset_weight))
        target = max(1.0 - float(policy.max_cash_weight), float(lower.sum()))
        if target > upper.sum() + tolerance:
            return PortfolioResult("infeasible", {}, None, None, {"reason": "Asset bounds cannot satisfy cash maximum"})
        weights = _project_box_simplex(np.full(count, target / count), lower, upper, target)
        spectral_radius = max(float(eigenvalues.max()), 0.0)
        iterations = 0
        if spectral_radius > tolerance:
            step = 1.0 / (2.0 * spectral_radius)
            for iterations in range(1, max_iterations + 1):
                candidate = _project_box_simplex(weights - step * (2.0 * matrix @ weights), lower, upper, target)
                if np.linalg.norm(candidate - weights, ord=np.inf) <= tolerance:
                    weights = candidate
                    break
                weights = candidate
            else:
                return PortfolioResult("failed_validation", {}, None, None, {"reason": "Solver did not converge", "iterations": max_iterations})
        cash = 1.0 - float(weights.sum())
        if cash < float(policy.min_cash_weight) - tolerance or cash > float(policy.max_cash_weight) + tolerance:
            return PortfolioResult("infeasible", {}, None, None, {"reason": "Cash bounds violated"})
        exact_target = max(Decimal(1) - policy.max_cash_weight, policy.min_asset_weight * count)
        result = {symbol: min(policy.max_asset_weight, max(policy.min_asset_weight, Decimal(str(round(weight, 12)))))
                  for symbol, weight in zip(policy.symbols, weights)}
        residual = exact_target - sum(result.values())
        original_residual = residual
        if abs(residual) > Decimal("0.000000001"):
            raise ValueError("Solver output differs materially from the exact asset target")
        for symbol in policy.symbols:
            adjustment = (min(residual, policy.max_asset_weight - result[symbol]) if residual >= 0 else
                          max(residual, policy.min_asset_weight - result[symbol]))
            result[symbol] += adjustment
            residual -= adjustment
            if residual == 0:
                break
        exact_cash = Decimal(1) - sum(result.values())
        if residual != 0 or not policy.min_cash_weight <= exact_cash <= policy.max_cash_weight:
            raise ValueError("Decimal allocation cannot reconcile within the unchanged bounds")
        vector = np.array([float(result[s]) for s in policy.symbols])
        variance = float(vector @ matrix @ vector)
        return PortfolioResult("success", result, exact_cash, variance,
                               {"solver": VERSION, "iterations": iterations, "decimal_residual_adjustment": str(original_residual),
                                "return_convention": "simple_close_to_close", "covariance_estimator": "sample_ddof_1",
                                "cash_treatment": "zero_variance_at_maximum_allowed_cash", "target_asset_weight": target})
    except ValueError as exc:
        return PortfolioResult("failed_validation", {}, None, None, {"reason": str(exc)})
