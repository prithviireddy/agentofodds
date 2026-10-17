"""Provider-independent contracts for the first daily-close fixture."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp requires an explicit timezone")
    return parsed.astimezone(timezone.utc)


def required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


@dataclass(frozen=True)
class DailyClose:
    symbol: str
    session: date
    close: Decimal
    available_at: datetime
    source_id: str

    @classmethod
    def from_dict(cls, row: dict) -> "DailyClose":
        symbol = required_text(row["symbol"], "symbol")
        source = required_text(row["source_id"], "source_id")
        raw_close = required_text(row["close"], "close")
        try:
            close = Decimal(raw_close)
        except InvalidOperation as exc:
            raise ValueError("close must be a decimal string") from exc
        if not close.is_finite() or close <= 0:
            raise ValueError("close must be finite and positive")
        session = date.fromisoformat(row["session"])
        available = timestamp(row["available_at"])
        if available.date() < session:
            raise ValueError("Price cannot be available before its session")
        return cls(symbol, session, close, available, source)
