"""Explicit investment-policy contract; no implicit risk defaults."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import re


class PolicyError(ValueError):
    pass


def decimal(value, field):
    try:
        parsed = Decimal(str(value))
    except Exception as exc:
        raise PolicyError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite():
        raise PolicyError(f"{field} must be finite")
    return parsed


@dataclass(frozen=True)
class InvestmentPolicy:
    schema_version: int
    policy_id: str
    as_of: datetime
    symbols: tuple[str, ...]
    capital: Decimal
    currency: str
    objective: str
    min_asset_weight: Decimal
    max_asset_weight: Decimal
    min_cash_weight: Decimal
    max_cash_weight: Decimal
    review_frequency: str

    def validate(self):
        if self.schema_version != 1:
            raise PolicyError("Unsupported policy schema version")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", self.policy_id):
            raise PolicyError("Invalid policy ID")
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise PolicyError("Policy cutoff requires timezone")
        if not self.symbols or len(set(self.symbols)) != len(self.symbols):
            raise PolicyError("Policy symbols must be nonempty and unique")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", symbol) for symbol in self.symbols):
            raise PolicyError("Invalid policy symbol")
        if decimal(self.capital, "capital") <= 0:
            raise PolicyError("capital must be positive")
        if self.currency != "USD":
            raise PolicyError("Only USD is supported in version 1")
        if self.objective not in ("minimum_variance",):
            raise PolicyError("Unsupported objective")
        if self.review_frequency not in ("monthly", "manual"):
            raise PolicyError("Unsupported review frequency")
        values = [decimal(value, name) for name, value in (
            ("min_asset_weight", self.min_asset_weight), ("max_asset_weight", self.max_asset_weight),
            ("min_cash_weight", self.min_cash_weight), ("max_cash_weight", self.max_cash_weight))]
        if any(value < 0 or value > 1 for value in values):
            raise PolicyError("Weights must be between zero and one")
        minimum, maximum, cash_minimum, cash_maximum = values
        if minimum > maximum or cash_minimum > cash_maximum:
            raise PolicyError("Weight bounds are reversed")
        count = Decimal(len(self.symbols))
        if count * minimum + cash_minimum > 1:
            raise PolicyError("Minimum weights make policy infeasible")
        if count * maximum + cash_maximum < 1:
            raise PolicyError("Maximum weights make policy infeasible")
        return self
