"""Validated numerical price-input contract; no provider SDK dependency."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import re
from backend.app.contracts.market_data import DailyClose


class NumericalInputError(ValueError):
    pass


@dataclass(frozen=True)
class PriceInput:
    schema_version: int
    as_of: datetime
    requested_symbols: tuple[str, ...]
    provider: str
    feed: str
    adjustment: str
    currency: str
    retrieved_at: datetime
    source_sha256: str
    availability_status: str
    bars: tuple[DailyClose, ...]
    missing_symbols: tuple[str, ...]
    status: str

    def validate(self):
        if self.schema_version != 1:
            raise NumericalInputError("Unsupported price-input schema version")
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None or self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise NumericalInputError("Cutoff and retrieval time require timezones")
        if not self.requested_symbols or len(set(self.requested_symbols)) != len(self.requested_symbols):
            raise NumericalInputError("Requested symbols must be nonempty and unique")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", symbol) for symbol in self.requested_symbols):
            raise NumericalInputError("Invalid requested symbol")
        if self.provider not in ("fixture", "alpaca") or not self.feed or self.adjustment not in ("none", "all") or self.currency != "USD":
            raise NumericalInputError("Unsupported price provenance")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise NumericalInputError("Invalid source hash")
        if self.availability_status not in ("verified", "not_verified"):
            raise NumericalInputError("Invalid availability status")
        actual_missing = tuple(symbol for symbol in self.requested_symbols if not any(bar.symbol == symbol for bar in self.bars))
        if self.missing_symbols != actual_missing:
            raise NumericalInputError("Missing-symbol status does not match bars")
        if self.status != ("success" if not actual_missing else "partial_data"):
            raise NumericalInputError("Price-input status does not match coverage")
        keys = [(bar.symbol, bar.session) for bar in self.bars]
        if len(keys) != len(set(keys)) or any(bar.symbol not in self.requested_symbols for bar in self.bars):
            raise NumericalInputError("Bars have duplicate or unexpected symbols")
        if any(not isinstance(bar.close, Decimal) or bar.close <= 0 for bar in self.bars):
            raise NumericalInputError("Bars have invalid close values")
        return self

    @property
    def point_in_time_eligible(self):
        return self.availability_status == "verified" and self.status == "success"
