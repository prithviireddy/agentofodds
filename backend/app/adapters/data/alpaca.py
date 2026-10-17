"""Bounded Alpaca historical daily-bar access proof; no trading endpoints."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

BARS_ENDPOINT = "https://data.alpaca.markets/v2/stocks/bars"


class AlpacaError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AlpacaMarketDataClient:
    """One read-only bars request per access proof. No retries or trading methods."""
    def __init__(self, key_id, secret_key, opener=None):
        if not key_id or not secret_key:
            raise AlpacaError("missing_configuration", "Set ALPACA_API_KEY and ALPACA_SECRET_KEY")
        if any("\r" in value or "\n" in value for value in (key_id, secret_key)):
            raise AlpacaError("failed_validation", "Alpaca credentials contain an invalid newline")
        self.key_id, self.secret_key = key_id, secret_key
        self.opener = opener or build_opener(NoRedirect()).open
        self.request_count = 0

    def daily_bars(self, symbols, start, end, feed="iex", adjustment="all"):
        if not symbols or len(set(symbols)) != len(symbols):
            raise ValueError("Symbols must be nonempty and unique")
        if any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", symbol) for symbol in symbols):
            raise ValueError("Invalid symbol")
        if feed != "iex" or adjustment != "all":
            raise ValueError("This proof requires feed=iex and adjustment=all")
        if not start.endswith("Z") or not end.endswith("Z"):
            raise ValueError("Start and end must be UTC timestamps")
        if self.request_count >= 1:
            raise AlpacaError("awaiting_quota", "One historical-bars request per proof run")
        query = urlencode({"symbols": ",".join(symbols), "timeframe": "1Day", "start": start,
                           "end": end, "feed": feed, "adjustment": adjustment})
        url = f"{BARS_ENDPOINT}?{query}"
        self.request_count += 1
        request = Request(url, headers={"APCA-API-KEY-ID": self.key_id,
                                         "APCA-API-SECRET-KEY": self.secret_key,
                                         "Accept": "application/json"})
        try:
            with self.opener(request, timeout=20) as response:
                body = response.read(20_000_001)
            if len(body) > 20_000_000:
                raise AlpacaError("failed_validation", "Alpaca response exceeds 20 MB limit")
            payload = json.loads(body, parse_float=Decimal)
            if not isinstance(payload, dict) or not isinstance(payload.get("bars"), dict):
                raise ValueError("Expected bars object")
            return payload, {"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                             "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                             "provider": "alpaca", "feed": feed, "adjustment": adjustment,
                             "timeframe": "1Day"}
        except HTTPError as exc:
            status = "awaiting_quota" if exc.code == 429 else "provider_error"
            raise AlpacaError(status, f"Alpaca HTTP {exc.code}; no automatic retry") from None
        except (URLError, TimeoutError, OSError):
            raise AlpacaError("provider_error", "Alpaca transport failed; no automatic retry") from None
        except (ValueError, UnicodeError):
            raise AlpacaError("failed_validation", "Alpaca returned invalid bars JSON") from None


def normalise_daily_bars(payload, requested_symbols):
    result, missing = [], []
    for symbol in requested_symbols:
        rows = payload["bars"].get(symbol, [])
        if not rows:
            missing.append(symbol)
            continue
        for row in rows:
            try:
                close = Decimal(str(row["c"]))
                timestamp = datetime.fromisoformat(row["t"].replace("Z", "+00:00"))
            except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid daily bar for {symbol}") from exc
            if timestamp.tzinfo is None or not close.is_finite() or close <= 0:
                raise ValueError(f"Invalid daily bar for {symbol}")
            result.append({"symbol": symbol, "session": timestamp.date().isoformat(), "close": str(close),
                           "bar_timestamp": timestamp.astimezone(timezone.utc).isoformat(),
                           "source_id": f"alpaca:{symbol}:{timestamp.isoformat()}:1Day:iex:all"})
    return sorted(result, key=lambda bar: (bar["symbol"], bar["session"])), missing
