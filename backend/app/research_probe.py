"""One bounded fundamental-research run over the local evidence index."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
import tomllib

from backend.app.adapters.llm_gemini import GeminiClient, ModelError
from backend.app.research.fundamental import PROMPT_VERSION, ResearchRequest, run_fundamental_research
from backend.app.retrieval.index import EvidenceIndexError, LocalEvidenceIndex
from backend.app.sec_probe import ROOT, load_dotenv


def _safe_report(report):
    return {
        "status": report.status,
        "symbol": report.symbol,
        "as_of": report.as_of,
        "findings": [asdict(finding) for finding in report.findings],
        "evidence": [{
            "chunk_id": hit.chunk_id, "source_id": hit.source_id, "source_sha256": hit.source_sha256,
            "symbol": hit.symbol, "published_at": hit.published_at, "score": hit.score,
        } for hit in report.evidence],
        "limitations": list(report.limitations),
        "prompt_version": report.prompt_version,
        "model_metadata": report.model_metadata,
        "diagnostics": report.diagnostics,
    }


def main():
    try:
        load_dotenv(ROOT / ".env")
        with (ROOT / "config/research.toml").open("rb") as file:
            config = tomllib.load(file)
        if config.get("schema_version") != 1 or config.get("prompt_version") != PROMPT_VERSION:
            raise ValueError("Unsupported research configuration")
        request = ResearchRequest(
            config["symbol"], datetime.fromisoformat(config["as_of"].replace("Z", "+00:00")),
            tuple(config["queries"]), config["top_k_per_query"],
        )
        index = LocalEvidenceIndex.load(ROOT / "data/evidence_index.json")
        report = run_fundamental_research(index, request, GeminiClient(os.environ.get("GEMINI_API_KEY")))
        output = {"schema_version": 1, "mode": "live_fundamental_research", **_safe_report(report)}
    except ModelError as exc:
        output = {"mode": "live_fundamental_research", "status": exc.status, "error": str(exc)}
    except (EvidenceIndexError, ValueError, KeyError, TypeError, OSError, tomllib.TOMLDecodeError) as exc:
        output = {"mode": "live_fundamental_research", "status": "failed_validation", "error": str(exc)}
    output["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(output, indent=2))
    return 0 if output["status"] in ("success", "insufficient_evidence") else 1


if __name__ == "__main__":
    raise SystemExit(main())
