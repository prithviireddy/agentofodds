"""Quantitative research role: computed descriptive evidence, never LLM arithmetic."""
from dataclasses import dataclass
from decimal import InvalidOperation
from backend.app.domain.statistics import calculate_price_statistics, PriceStatistics


@dataclass(frozen=True)
class QuantitativeReport:
    status: str
    as_of: str
    symbols: tuple[str, ...]
    statistics: PriceStatistics | None
    provenance: dict
    limitations: tuple[str, ...]
    diagnostics: dict


def run_quantitative_research(prices, *, max_age_days):
    """Freshness is a caller-selected calendar-day limit, not a risk-profile default."""
    provenance = {name: getattr(prices, name) for name in
                  ("provider", "feed", "adjustment", "currency", "source_sha256", "availability_status")}
    provenance.update(retrieved_at=prices.retrieved_at.isoformat(),
                      source_ids=tuple(bar.source_id for bar in prices.bars),
                      calculation_version="price-statistics-v1")
    limits = (
        "Descriptive historical price measures are not return forecasts or portfolio weights.",
        "Simple returns use intersected sessions; sample covariance uses ddof=1. No annualisation.",
        "Values are fractions, volatility per observed interval; gaps are not trading-calendar validated.",
        "Corporate-action correctness and dividend-inclusive total returns are not established.",
    ) + (("Synthetic fixture prices, not actual investment performance.",) if prices.provider == "fixture" else ())
    diagnostics = {"model_called": False, "max_age_days": max_age_days}

    def report(status, statistics=None, extra=()):
        return QuantitativeReport(status, prices.as_of.isoformat(), prices.requested_symbols,
                                  statistics, provenance, limits + tuple(extra), diagnostics)
    try:
        if type(max_age_days) is not int or max_age_days < 0:
            raise ValueError("max_age_days must be an explicit nonnegative integer")
        prices.validate()
        if prices.missing_symbols:
            return report("insufficient_evidence", extra=("Missing prices for: " + ", ".join(prices.missing_symbols),))
        if prices.availability_status != "verified":
            return report("insufficient_evidence", extra=("Historical price availability is unverified.",))
        statistics = calculate_price_statistics(prices)
        from datetime import date
        latest = date.fromisoformat(statistics.return_sessions[-1])
        if (prices.as_of.date() - latest).days > max_age_days:
            return report("stale_data", extra=("Latest common session exceeds the declared freshness limit.",))
        return report("success", statistics)
    except (ValueError, TypeError, InvalidOperation, FloatingPointError) as exc:
        return report("failed_validation", extra=(str(exc),))
