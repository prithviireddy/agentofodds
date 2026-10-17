"""Bounded retrieval of configured SEC filing and investor-relations evidence."""
from datetime import datetime, timezone
import hashlib
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler


class EvidenceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sec_filing_url(cik, accession, document):
    if not re.fullmatch(r"[0-9]{10}", cik):
        raise ValueError("Invalid filing CIK")
    if not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", accession):
        raise ValueError("Invalid filing accession")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", document) or document in (".", ".."):
        raise ValueError("Unsafe filing document")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{document}"


def allowed_release_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "www.microsoft.com":
        raise ValueError("Release source host is not allowlisted")
    if parsed.query or parsed.fragment or not re.fullmatch(r"/en-us/investor/[A-Za-z0-9/_-]+", parsed.path):
        raise ValueError("Release source path is not allowlisted")
    return url


class EvidenceClient:
    """At most two configured, read-only document fetches; documents are data only."""
    def __init__(self, user_agent, opener=None):
        if not user_agent or "\r" in user_agent or "\n" in user_agent:
            raise EvidenceError("missing_configuration", "Set SEC_USER_AGENT for the SEC filing request")
        self.user_agent = user_agent
        self.opener = opener or build_opener(NoRedirect()).open
        self.request_count = 0

    def fetch_html(self, url, source_type):
        if source_type not in ("sec_filing", "investor_release"):
            raise ValueError("Unknown evidence source type")
        if self.request_count >= 2:
            raise EvidenceError("awaiting_quota", "Two document fetches per proof run")
        self.request_count += 1
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"})
        try:
            with self.opener(request, timeout=20) as response:
                body = response.read(10_000_001)
            if len(body) > 10_000_000:
                raise EvidenceError("failed_validation", "Evidence response exceeds 10 MB limit")
        except HTTPError as exc:
            status = "awaiting_quota" if exc.code == 429 else "provider_error"
            raise EvidenceError(status, f"Evidence HTTP {exc.code}; no automatic retry") from None
        except (URLError, TimeoutError, OSError):
            raise EvidenceError("provider_error", "Evidence transport failed; no automatic retry") from None
        text = body.decode("utf-8", errors="replace")
        if not text.strip():
            raise EvidenceError("failed_validation", "Evidence response is empty")
        return text, {"source_type": source_type, "url": url,
                      "retrieved_at": datetime.now(timezone.utc).isoformat(),
                      "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def visible_text(html):
    without_scripts = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", without_scripts)).strip()


def evidence_record(html, metadata, symbol, published_at, expected_text=()):
    text = visible_text(html)
    if len(text) < 200:
        raise ValueError("Evidence text is too short")
    absent = [phrase for phrase in expected_text if phrase not in text]
    if absent:
        raise ValueError("Evidence did not contain expected date/title markers")
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    return {**metadata, "symbol": symbol, "published_at": published_at,
            "content_length": len(text), "title": visible_text(title_match.group(1)) if title_match else None,
            "source_id": f"{metadata['source_type']}:{symbol}:{metadata['sha256']}",
            "content_stored": False}
