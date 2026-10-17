"""Offline synthetic daily-close adapter. Never substitutes for live proof."""
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from backend.app.contracts.market_data import DailyClose, timestamp


@dataclass(frozen=True)
class PriceResult:
    status: str
    bars: tuple[DailyClose, ...]
    missing_symbols: tuple[str, ...]
    excluded_after_cutoff: int
    metadata: dict


def load_prices(path: Path, symbols: tuple[str, ...], as_of: datetime,
                start: date, end: date) -> PriceResult:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("Cutoff requires an explicit timezone")
    if start > end:
        raise ValueError("Price window start must not exceed end")
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("Requested symbols must be nonempty and unique")
    content = path.read_bytes()
    raw = json.loads(content)
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("Unsupported fixture schema version")
    expected = {"kind": "synthetic", "provider": "fixture", "currency": "USD",
                "feed": "synthetic-daily-close", "adjustment": "none"}
    for key, value in expected.items():
        if raw[key] != value:
            raise ValueError(f"Unsupported fixture {key}: expected {value}")
    # Artifact creation time is not historical market retrieval time.
    timestamp(raw["created_at"])
    bars = tuple(DailyClose.from_dict(row) for row in raw["bars"])
    keys = [(bar.symbol, bar.session) for bar in bars]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate symbol/session prices")
    if len({bar.source_id for bar in bars}) != len(bars):
        raise ValueError("Duplicate price source IDs")
    candidates = [bar for bar in bars if bar.symbol in symbols and start <= bar.session <= end]
    selected = tuple(sorted((bar for bar in candidates if bar.available_at <= as_of),
                            key=lambda bar: (bar.symbol, bar.session)))
    missing = tuple(symbol for symbol in symbols if not any(bar.symbol == symbol for bar in selected))
    metadata = {**expected, "schema_version": 1, "created_at": raw["created_at"],
                "sha256": hashlib.sha256(content).hexdigest(),
                "as_of": as_of.isoformat(), "start": start.isoformat(), "end": end.isoformat(),
                "limitation": "Synthetic values; no corporate actions, exchange calendar or completeness guarantee."}
    return PriceResult("partial_data" if missing else "success", selected, missing,
                       len(candidates) - len(selected), metadata)
