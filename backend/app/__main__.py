"""Inspect offline fixtures with a configurable universe and cutoff."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys
from backend.app.adapters.data.fixture import load_prices
from backend.app.config.universe import load_universe
from backend.app.contracts.market_data import timestamp

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", type=Path, default=ROOT / "config/universe.toml")
    parser.add_argument("--prices", type=Path, default=ROOT / "fixtures/prices.json")
    parser.add_argument("--as-of", help="Timezone-aware cutoff; defaults to universe configuration")
    parser.add_argument("--start", default="2025-01-30")
    parser.add_argument("--end", default="2025-01-31")
    args = parser.parse_args()
    try:
        universe = load_universe(args.universe)
        cutoff = timestamp(args.as_of) if args.as_of else universe.as_of
        result = load_prices(args.prices, universe.symbols, cutoff,
                             date.fromisoformat(args.start), date.fromisoformat(args.end))
        output = {"project": "Agent of Odds", "mode": "fixture", "status": result.status,
                  "universe": universe.name, "symbols": universe.symbols,
                  "provider_access": "unverified", "metadata": result.metadata,
                  "bar_count": len(result.bars), "missing_symbols": result.missing_symbols,
                  "excluded_after_cutoff": result.excluded_after_cutoff,
                  "bars": [{"symbol": bar.symbol, "session": bar.session.isoformat(),
                            "close": str(bar.close), "available_at": bar.available_at.isoformat(),
                            "source_id": bar.source_id} for bar in result.bars]}
        print(json.dumps(output, indent=2))
        return 0 if result.status == "success" else 1
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        print(json.dumps({"mode": "fixture", "status": "failed_validation", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
