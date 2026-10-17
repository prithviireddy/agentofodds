"""Load a configurable development universe without provider dependencies."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import tomllib
from backend.app.contracts.market_data import required_text, timestamp
from backend.app.adapters.data.sec import cik_string


@dataclass(frozen=True)
class Company:
    symbol: str
    name: str
    sector: str
    rationale: str
    sec_cik: str


@dataclass(frozen=True)
class Universe:
    name: str
    as_of: datetime
    selection_rationale: str
    companies: tuple[Company, ...]

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(company.symbol for company in self.companies)


def load_universe(path: Path) -> Universe:
    with path.open("rb") as file:
        raw = tomllib.load(file)
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("Unsupported universe schema version")
    companies = tuple(Company(**{
        **{field: required_text(row[field], field)
           for field in ("symbol", "name", "sector", "rationale")},
        "sec_cik": cik_string(row["sec_cik"]),
    }) for row in raw["companies"])
    if not companies:
        raise ValueError("Universe must contain at least one company")
    symbols = [company.symbol for company in companies]
    ciks = [company.sec_cik for company in companies]
    if len(set(symbols)) != len(symbols) or len(set(ciks)) != len(ciks):
        raise ValueError("Duplicate company symbols or SEC CIKs")
    if any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", symbol) for symbol in symbols):
        raise ValueError("Invalid company symbol")
    return Universe(required_text(raw["name"], "name"), timestamp(raw["as_of"]),
                    required_text(raw["selection_rationale"], "selection_rationale"), companies)
