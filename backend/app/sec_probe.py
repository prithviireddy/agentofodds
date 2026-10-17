"""Explicit live SEC access proof; no price/news/model calls."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from backend.app.adapters.data.sec import SecClient, SecError, TICKERS, audit_ticker_mapping, eligible_assets, eligible_filings
from backend.app.config.universe import load_universe

ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding shell configuration."""
    if not path.exists():
        return
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}")
        key, value = line.split("=", 1)
        if not key.isidentifier():
            raise ValueError(f"Invalid .env key on line {line_number}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def run(universe, client):
    tickers, provenance = client.fetch(TICKERS)
    companies = []
    for company in universe.companies:
        cik = company.sec_cik
        facts, fact_source = client.fetch(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        filings, filing_source = client.fetch(f"https://data.sec.gov/submissions/CIK{cik}.json")
        assets = eligible_assets(facts, cik, universe.as_of)
        documents = eligible_filings(filings, cik, universe.as_of)
        companies.append({"symbol": company.symbol, "name": company.name, "cik": cik,
                          "ticker_audit": audit_ticker_mapping(tickers, company.symbol, cik),
                          "status": "success" if assets and documents else "partial_data",
                          "asset_sample": assets[-1] if assets else None,
                          "filing_metadata_sample": documents[-1] if documents else None,
                          "provenance": [fact_source, filing_source]})
    return {"schema_version": 1, "mode": "live_access_proof",
            "status": "success" if all(c["status"] == "success" for c in companies) else "partial_data",
            "as_of": universe.as_of.isoformat(), "ticker_audit_source": provenance, "companies": companies,
            "limitations": ["Assets in USD only; no ratios or financial-statement harmonisation.",
                           "Current ticker mappings can be ambiguous and do not establish historical membership.",
                           "Filing dates use next-day 05:00 UTC as a conservative availability proxy.",
                           "Current SEC snapshots can contain corrections; this is not a certified point-in-time dataset.",
                           "Recent submission metadata only; older submission files are not fetched.",
                           "Filing bodies, prices, news and model access are not verified by this probe."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", type=Path, default=ROOT / "config/universe.toml")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    try:
        load_dotenv(args.env_file)
        universe = load_universe(args.universe)
        client = SecClient(os.environ.get("SEC_USER_AGENT"))
        result = run(universe, client)
    except SecError as exc:
        result = {"status": exc.status, "mode": "live_access_proof", "error": str(exc)}
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        result = {"status": "failed_validation", "mode": "live_access_proof", "error": str(exc)}
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
