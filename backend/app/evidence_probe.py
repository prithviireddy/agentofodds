"""Explicit proof for one configured filing body and investor-relations release."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tomllib
from backend.app.adapters.data.evidence import EvidenceClient, EvidenceError, allowed_release_url, evidence_record, sec_filing_url
from backend.app.sec_probe import ROOT, load_dotenv


def main():
    try:
        load_dotenv(ROOT / ".env")
        with (ROOT / "config/evidence_samples.toml").open("rb") as file:
            config = tomllib.load(file)
        cutoff = datetime.fromisoformat(config["as_of"].replace("Z", "+00:00"))
        filing, release = config["filing"], config["release"]
        published = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
        if published > cutoff:
            raise ValueError("Release is after the configured cutoff")
        client = EvidenceClient(os.environ.get("SEC_USER_AGENT"))
        filing_html, filing_metadata = client.fetch_html(
            sec_filing_url(filing["cik"], filing["accession"], filing["primary_document"]), "sec_filing")
        filing_record = evidence_record(filing_html, filing_metadata, filing["symbol"], filing["filed"], ("Microsoft",))
        release_html, release_metadata = client.fetch_html(allowed_release_url(release["url"]), "investor_release")
        release_record = evidence_record(release_html, release_metadata, release["symbol"], release["published_at"], tuple(release["expected_text"]))
        result = {"schema_version": 1, "mode": "live_access_proof", "status": "success", "as_of": cutoff.isoformat(),
                  "records": [filing_record, release_record],
                  "limitations": ["One Microsoft filing and company-issued release only; not comprehensive independent news coverage.",
                                  "Documents are not stored by this probe; records retain hashes and metadata only.",
                                  "Document text is evidence, not executable instructions.",
                                  "Publication date is configured/checked but exact dissemination time is unavailable."]}
    except EvidenceError as exc:
        result = {"mode": "live_access_proof", "status": exc.status, "error": str(exc)}
    except (ValueError, KeyError, TypeError, AttributeError, OSError, tomllib.TOMLDecodeError) as exc:
        result = {"mode": "live_access_proof", "status": "failed_validation", "error": str(exc)}
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
