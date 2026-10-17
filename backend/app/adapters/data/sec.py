"""Bounded SEC JSON access and conservative access-proof normalisation."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

TICKERS = "https://www.sec.gov/files/company_tickers.json"


class SecError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def cik_string(value):
    value = str(value)
    if not re.fullmatch(r"[0-9]{1,10}", value) or int(value) == 0:
        raise ValueError("Invalid SEC CIK")
    return value.zfill(10)


class SecClient:
    """Sequential use only. One request/second, 12 requests/run, no retries."""
    def __init__(self, user_agent, opener=None, sleep=time.sleep, clock=time.monotonic):
        if not user_agent or not re.fullmatch(r"[^\r\n]+\s+[^\s@]+@[^\s@]+\.[^\s@]+", user_agent):
            raise SecError("missing_configuration", "Set SEC_USER_AGENT to application name and contact email")
        self.user_agent = user_agent
        self.opener = opener or build_opener(NoRedirect()).open
        self.sleep, self.clock = sleep, clock
        self.count, self.last = 0, None

    def fetch(self, url):
        allowed = (url == TICKERS or re.fullmatch(
            r"https://data\.sec\.gov/(submissions/CIK[0-9]{10}\.json|api/xbrl/companyfacts/CIK[0-9]{10}\.json)", url))
        if not allowed:
            raise SecError("failed_validation", "SEC endpoint is not allowlisted")
        if self.count >= 12:
            raise SecError("awaiting_quota", "SEC per-run request budget exhausted")
        if self.last is not None:
            self.sleep(max(0, 1 - (self.clock() - self.last)))
        self.count += 1
        self.last = self.clock()
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        try:
            with self.opener(request, timeout=20) as response:
                body = response.read(25_000_001)
            if len(body) > 25_000_000:
                raise SecError("failed_validation", "SEC response exceeds 25 MB limit")
            payload = json.loads(body, parse_float=Decimal)
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            return payload, {"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                             "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        except HTTPError as exc:
            status = "awaiting_quota" if exc.code == 429 else "provider_error"
            raise SecError(status, f"SEC HTTP {exc.code}; no automatic retry") from None
        except (URLError, TimeoutError, OSError):
            raise SecError("provider_error", "SEC transport failed; no automatic retry") from None
        except (ValueError, UnicodeError):
            raise SecError("failed_validation", "SEC returned invalid JSON") from None


def resolve_symbols(payload, symbols):
    result = {}
    for symbol in symbols:
        rows = [row for row in payload.values() if row.get("ticker") == symbol]
        if len(rows) != 1:
            raise ValueError(f"Expected one SEC ticker mapping for {symbol}")
        row = rows[0]
        result[symbol] = {"cik": cik_string(row["cik_str"]), "sec_name": row["title"]}
    return result


def conservative_availability(filed):
    # SEC filed is a date, not an intraday timestamp. Wait through the full
    # US Eastern filing day using UTC-5 even in summer (conservative by 1h).
    return datetime.combine(date.fromisoformat(filed) + timedelta(days=1),
                            datetime.min.time(), timezone.utc) + timedelta(hours=5)


def eligible_assets(payload, cik, cutoff):
    if cutoff.tzinfo is None:
        raise ValueError("Cutoff must be timezone-aware")
    if cik_string(payload["cik"]) != cik_string(cik):
        raise ValueError("CompanyFacts CIK mismatch")
    rows = payload.get("facts", {}).get("us-gaap", {}).get("Assets", {}).get("units", {}).get("USD", [])
    eligible = []
    for row in rows:
        if row.get("form") not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        available = conservative_availability(row["filed"])
        end = date.fromisoformat(row["end"])
        if end > date.fromisoformat(row["filed"]):
            raise ValueError("Fact period ends after filing")
        value = Decimal(str(row["val"]))
        if not value.is_finite() or value < 0:
            raise ValueError("Invalid Assets value")
        accession = row["accn"]
        if not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", accession):
            raise ValueError("Invalid accession")
        if available <= cutoff:
            eligible.append({"concept": "us-gaap:Assets", "value": str(value), "unit": "USD",
                             "period_end": row["end"], "filed": row["filed"], "form": row["form"],
                             "accession": accession, "available_at": available.isoformat(),
                             "availability_basis": "conservative_filing_date",
                             "source_id": f"sec:{cik_string(cik)}:{accession}:us-gaap:Assets:USD:{row['end']}"})
    return sorted(eligible, key=lambda row: (row["period_end"], row["filed"], row["accession"]))


def eligible_filings(payload, cik, cutoff):
    if cutoff.tzinfo is None:
        raise ValueError("Cutoff must be timezone-aware")
    if cik_string(payload["cik"]) != cik_string(cik):
        raise ValueError("Submissions CIK mismatch")
    recent = payload["filings"]["recent"]
    fields = ("accessionNumber", "filingDate", "form", "primaryDocument")
    if len({len(recent[field]) for field in fields}) != 1:
        raise ValueError("Submissions arrays have unequal lengths")
    result = []
    for accession, filed, form, document in zip(*(recent[field] for field in fields)):
        if form not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        if not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", accession):
            raise ValueError("Invalid filing accession")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", document) or document in (".", ".."):
            raise ValueError("Unsafe primary document name")
        available = conservative_availability(filed)
        if available <= cutoff:
            result.append({"accession": accession, "filed": filed, "form": form,
                           "available_at": available.isoformat(),
                           "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{document}"})
    return sorted(result, key=lambda row: (row["filed"], row["accession"]))


def audit_ticker_mapping(payload, symbol, expected_cik):
    """Report current SEC ticker collisions without choosing an issuer from them."""
    matches = [{"cik": cik_string(row["cik_str"]), "sec_name": row["title"]}
               for row in payload.values() if row.get("ticker") == symbol]
    configured = cik_string(expected_cik)
    return {"symbol": symbol, "configured_cik": configured, "current_matches": matches,
            "configured_cik_present": any(row["cik"] == configured for row in matches)}
