"""Return and covariance calculations independent of providers and LLMs."""
from dataclasses import dataclass
import numpy as np
from backend.app.domain.numerical_inputs import PriceInput, NumericalInputError


@dataclass(frozen=True)
class ReturnSeries:
    symbols: tuple[str, ...]
    sessions: tuple[str, ...]
    values: np.ndarray
    convention: str = "simple_close_to_close"


def aligned_simple_returns(prices: PriceInput) -> ReturnSeries:
    prices.validate()
    if not prices.point_in_time_eligible:
        raise NumericalInputError("Prices are not eligible for point-in-time returns")
    by_symbol = {symbol: {bar.session: float(bar.close) for bar in prices.bars if bar.symbol == symbol}
                 for symbol in prices.requested_symbols}
    sessions = tuple(sorted(set.intersection(*(set(by_symbol[symbol]) for symbol in prices.requested_symbols))))
    if len(sessions) < 3:
        raise NumericalInputError("At least three aligned sessions are required for covariance")
    close = np.array([[by_symbol[symbol][session] for symbol in prices.requested_symbols] for session in sessions], dtype=float)
    if not np.isfinite(close).all() or (close <= 0).any():
        raise NumericalInputError("Close matrix has invalid values")
    values = close[1:] / close[:-1] - 1.0
    return ReturnSeries(prices.requested_symbols, tuple(session.isoformat() for session in sessions[1:]), values)


def sample_covariance(returns: ReturnSeries) -> np.ndarray:
    if returns.values.ndim != 2 or returns.values.shape[0] < 2:
        raise NumericalInputError("At least two returns are required for sample covariance")
    covariance = np.cov(returns.values, rowvar=False, ddof=1)
    covariance = np.atleast_2d(np.asarray(covariance, dtype=float))
    if covariance.shape != (len(returns.symbols), len(returns.symbols)) or not np.isfinite(covariance).all():
        raise NumericalInputError("Covariance calculation failed")
    return covariance
