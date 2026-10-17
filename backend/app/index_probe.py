"""Build a local evidence index from the two bounded M0.4 sources."""
from datetime import datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import tomllib

from backend.app.adapters.data.evidence import EvidenceClient, EvidenceError, allowed_release_url, sec_filing_url, visible_text
from backend.app.retrieval.index import EvidenceDocument, LocalEvidenceIndex
from backend.app.sec_probe import ROOT, load_dotenv


def _timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    try:
        load_dotenv(ROOT / ".env")
        with (ROOT / "config/evidence_samples.toml").open("rb") as file:
            config = tomllib.load(file)
        cutoff = _timestamp(config["as_of"])
        filing, release = config["filing"], config["release"]
        client = EvidenceClient(os.environ.get("SEC_USER_AGENT"))
        filing_url = sec_filing_url(filing["cik"], filing["accession"], filing["primary_document"])
        filing_html, filing_meta = client.fetch_html(filing_url, "sec_filing")
        release_url = allowed_release_url(release["url"])
        release_html, release_meta = client.fetch_html(release_url, "investor_release")
        filed = datetime.combine(datetime.fromisoformat(filing["filed"]).date() + timedelta(days=1), time(5), timezone.utc)
        documents = (
            EvidenceDocument(f"sec_filing:{filing['symbol']}:{filing_meta['sha256']}", filing["symbol"], "sec_filing",
                             filed, _timestamp(filing_meta["retrieved_at"]), filing_url, filing_meta["sha256"], visible_text(filing_html)),
            EvidenceDocument(f"investor_release:{release['symbol']}:{release_meta['sha256']}", release["symbol"], "investor_release",
                             _timestamp(release["published_at"]), _timestamp(release_meta["retrieved_at"]), release_url,
                             release_meta["sha256"], visible_text(release_html)),
        )
        if any(document.published_at > cutoff for document in documents):
            raise ValueError("Configured evidence is after the corpus cutoff")
        index = LocalEvidenceIndex.build(documents)
        output = ROOT / "data/evidence_index.json"
        index.save(output)
        sample = index.search("cloud revenue operating income", symbols=("MSFT",), published_before=cutoff, top_k=3)
        result = {
            "schema_version": 1, "mode": "live_index_proof", "status": "success",
            "index_path": str(output.relative_to(ROOT)), "retriever": "tfidf_cosine_v1",
            "documents": len(index.documents), "chunks": len(index.chunks),
            "source_versions": {document.source_id: document.source_sha256 for document in documents},
            "sample_hits": [{"chunk_id": hit.chunk_id, "source_id": hit.source_id, "score": hit.score} for hit in sample],
            "limitations": ["Lexical TF-IDF baseline; not embedding-based semantic search.",
                            "Two Microsoft sources only; not representative company coverage.",
                            "Index is local ignored data and must be rebuilt from versioned sources."],
        }
    except EvidenceError as exc:
        result = {"mode": "live_index_proof", "status": exc.status, "error": str(exc)}
    except (ValueError, KeyError, TypeError, OSError, tomllib.TOMLDecodeError) as exc:
        result = {"mode": "live_index_proof", "status": "failed_validation", "error": str(exc)}
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
