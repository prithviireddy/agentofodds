"""Explicit read-only Alpaca daily-price access proof."""
import json
import os
from pathlib import Path
from backend.app.adapters.data.alpaca import AlpacaError, AlpacaMarketDataClient, normalise_daily_bars
from backend.app.config.universe import load_universe
from backend.app.sec_probe import ROOT, load_dotenv


def main():
    try:
        load_dotenv(ROOT / ".env")
        universe = load_universe(ROOT / "config/universe.toml")
        client = AlpacaMarketDataClient(os.environ.get("ALPACA_API_KEY"),
                                       os.environ.get("ALPACA_SECRET_KEY"))
        payload, provenance = client.daily_bars(universe.symbols,
            "2025-01-30T00:00:00Z", "2025-02-01T00:00:00Z")
        bars, missing = normalise_daily_bars(payload, universe.symbols)
        result = {"schema_version": 1, "mode": "live_access_proof", "status": "success" if not missing else "partial_data",
                  "as_of": universe.as_of.isoformat(), "bar_count": len(bars), "missing_symbols": missing,
                  "bars": bars, "provenance": provenance,
                  "limitations": ["Read-only Market Data API proof; no Trading API orders were requested.",
                                  "IEX feed and adjustment=all are requested explicitly.",
                                  "Provider response does not establish historical publication availability; bars are not eligible for point-in-time evaluation yet.",
                                  "No corporate-action, exchange-calendar, news or model validation is performed."]}
    except AlpacaError as exc:
        result = {"mode": "live_access_proof", "status": exc.status, "error": str(exc)}
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        result = {"mode": "live_access_proof", "status": "failed_validation", "error": str(exc)}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
