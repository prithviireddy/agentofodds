"""Deterministic descriptive price statistics; no model or provider imports."""
from dataclasses import dataclass
import numpy as np
from backend.app.domain.numerical_inputs import NumericalInputError
from backend.app.domain.returns import aligned_simple_returns, sample_covariance


@dataclass(frozen=True)
class PriceStatistics:
    symbols: tuple[str, ...]
    return_sessions: tuple[str, ...]
    observation_count: int
    mean_simple_return: tuple[float, ...]
    sample_volatility: tuple[float, ...]
    cumulative_return: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]


def calculate_price_statistics(prices):
    prices.validate()
    for bar in prices.bars:
        if (bar.available_at.tzinfo is None or bar.available_at.utcoffset() is None
                or bar.available_at > prices.as_of or bar.session > prices.as_of.date()
                or bar.available_at.date() < bar.session or not bar.source_id
                or not bar.close.is_finite()):
            raise NumericalInputError("Invalid or future price observation")
    returns = aligned_simple_returns(prices)
    covariance = sample_covariance(returns)
    with np.errstate(over="raise", invalid="raise"):
        mean = returns.values.mean(axis=0)
        volatility = np.sqrt(np.diag(covariance))
        cumulative = np.prod(1 + returns.values, axis=0) - 1
    if not all(np.isfinite(values).all() for values in (mean, volatility, cumulative, covariance)):
        raise NumericalInputError("Nonfinite numerical statistics")
    return PriceStatistics(returns.symbols, returns.sessions, len(returns.sessions),
                           tuple(map(float, mean)), tuple(map(float, volatility)),
                           tuple(map(float, cumulative)), tuple(tuple(map(float, row)) for row in covariance))
