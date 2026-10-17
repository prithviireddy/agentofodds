"""Point-in-time hold-period evaluation and a constraint-compatible baseline."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from backend.app.domain.numerical_inputs import PriceInput
from backend.app.domain.optimizer import PortfolioResult
from backend.app.domain.policy import InvestmentPolicy, PolicyError, decimal


class EvaluationError(ValueError):
    pass


@dataclass(frozen=True)
class EvaluationPlan:
    schema_version: int
    decision_at: datetime
    execution_session: date
    valuation_session: date
    transaction_cost_bps: Decimal
    execution_convention: str
    valuation_convention: str

    def validate(self):
        if self.schema_version != 1:
            raise EvaluationError("Unsupported evaluation-plan schema version")
        if self.decision_at.tzinfo is None or self.decision_at.utcoffset() is None:
            raise EvaluationError("Decision time requires a timezone")
        if self.execution_session <= self.decision_at.date():
            raise EvaluationError("Execution must use a session after the decision date")
        if self.valuation_session <= self.execution_session:
            raise EvaluationError("Valuation must use a session after execution")
        costs = decimal(self.transaction_cost_bps, "transaction_cost_bps")
        if costs < 0:
            raise EvaluationError("Transaction costs cannot be negative")
        if self.execution_convention != "next_session_close":
            raise EvaluationError("Unsupported execution convention")
        if self.valuation_convention != "close_to_close_total_value_excluding_dividends":
            raise EvaluationError("Unsupported valuation convention")
        return self


@dataclass(frozen=True)
class PortfolioEvaluation:
    status: str
    strategy: str
    gross_return: Decimal | None
    transaction_cost: Decimal | None
    net_return: Decimal | None
    diagnostics: dict


@dataclass(frozen=True)
class EvaluationComparison:
    optimized: PortfolioEvaluation
    equal_weight: PortfolioEvaluation
    net_return_difference: Decimal | None


def equal_weight_portfolio(policy: InvestmentPolicy) -> PortfolioResult:
    """Create an equal-weight baseline under the optimizer's cash convention."""
    try:
        policy.validate()
    except PolicyError as exc:
        return PortfolioResult("infeasible", {}, None, None, {"reason": str(exc)})
    count = Decimal(len(policy.symbols))
    asset_total = max(Decimal("1") - policy.max_cash_weight, count * policy.min_asset_weight)
    weight = asset_total / count
    if weight > policy.max_asset_weight:
        return PortfolioResult("infeasible", {}, None, None, {"reason": "Equal weights violate asset maximum"})
    cash = Decimal("1") - asset_total
    return PortfolioResult(
        "success",
        {symbol: weight for symbol in policy.symbols},
        cash,
        None,
        {"strategy": "equal_weight_v1", "cash_treatment": "maximum_allowed_cash"},
    )


def evaluate_hold_period(
    strategy: str,
    portfolio: PortfolioResult,
    policy: InvestmentPolicy,
    prices: PriceInput,
    plan: EvaluationPlan,
) -> PortfolioEvaluation:
    """Evaluate fixed weights without allowing prices known at the decision cutoff."""
    try:
        policy.validate()
        prices.validate()
        plan.validate()
        if policy.as_of != plan.decision_at:
            raise EvaluationError("Policy cutoff must equal the evaluation decision time")
        if not prices.point_in_time_eligible:
            raise EvaluationError("Evaluation prices are not point-in-time eligible")
        if prices.as_of < max(bar.available_at for bar in prices.bars):
            raise EvaluationError("A price was unavailable at the evaluation cutoff")
        if prices.as_of.date() < plan.valuation_session:
            raise EvaluationError("Evaluation cutoff precedes the valuation session")
        if portfolio.status != "success" or portfolio.cash_weight is None:
            raise EvaluationError("Portfolio is not a successful allocation")
        if set(portfolio.weights) != set(policy.symbols):
            raise EvaluationError("Portfolio symbols do not match policy")
        weights = {symbol: decimal(value, f"weight[{symbol}]") for symbol, value in portfolio.weights.items()}
        cash = decimal(portfolio.cash_weight, "cash_weight")
        if any(value < 0 for value in weights.values()) or cash < 0:
            raise EvaluationError("Portfolio weights cannot be negative")
        if abs(sum(weights.values(), cash) - Decimal("1")) > Decimal("0.000000001"):
            raise EvaluationError("Portfolio weights do not sum to one")
        bars = {(bar.symbol, bar.session): bar for bar in prices.bars}
        required = [(symbol, session) for symbol in policy.symbols for session in (plan.execution_session, plan.valuation_session)]
        missing = [f"{symbol}:{session.isoformat()}" for symbol, session in required if (symbol, session) not in bars]
        if missing:
            raise EvaluationError("Missing execution or valuation prices: " + ", ".join(missing))
        if any(bars[key].available_at > prices.as_of for key in required):
            raise EvaluationError("An execution or valuation price was unavailable at the evaluation cutoff")
        invested_end = sum(
            weights[symbol] * bars[(symbol, plan.valuation_session)].close / bars[(symbol, plan.execution_session)].close
            for symbol in policy.symbols
        )
        gross_return = cash + invested_end - Decimal("1")
        transaction_cost = sum(weights.values()) * plan.transaction_cost_bps / Decimal("10000")
        net_return = gross_return - transaction_cost
        return PortfolioEvaluation(
            "success", strategy, gross_return, transaction_cost, net_return,
            {
                "decision_at": plan.decision_at.isoformat(),
                "execution_session": plan.execution_session.isoformat(),
                "valuation_session": plan.valuation_session.isoformat(),
                "execution_convention": plan.execution_convention,
                "valuation_convention": plan.valuation_convention,
                "transaction_cost_bps": str(plan.transaction_cost_bps),
                "dividends_included": False,
            },
        )
    except (EvaluationError, PolicyError, ValueError) as exc:
        return PortfolioEvaluation("failed_validation", strategy, None, None, None, {"reason": str(exc)})


def compare_with_equal_weight(
    optimized: PortfolioResult,
    policy: InvestmentPolicy,
    prices: PriceInput,
    plan: EvaluationPlan,
) -> EvaluationComparison:
    optimized_result = evaluate_hold_period("minimum_variance", optimized, policy, prices, plan)
    baseline_result = evaluate_hold_period("equal_weight", equal_weight_portfolio(policy), policy, prices, plan)
    difference = None
    if optimized_result.net_return is not None and baseline_result.net_return is not None:
        difference = optimized_result.net_return - baseline_result.net_return
    return EvaluationComparison(optimized_result, baseline_result, difference)
