"""One bounded Gemini structured-output proof using M0 evidence metadata only."""
import json
import os
from pathlib import Path
import tomllib
from backend.app.adapters.llm_gemini import GeminiClient, ModelError, validate_m0_output
from backend.app.sec_probe import ROOT, load_dotenv

SOURCES = [
    "sec_filing:MSFT:253a2c005df27df63ef3671e43b4bff0b976bb0049682d6d2f95c1c9308a8937",
    "investor_release:MSFT:6768cb420f41e963abb23fe73f2b28a2d03191749770cddd8ded61af7b569651",
]


def prompt():
    return """You are validating a research workflow. Return JSON only.
Company: MSFT
Evidence source IDs supplied: %s
Only source metadata and IDs are supplied; no document passages are supplied. Do not infer company performance, make investment advice, or claim that a source supports a fact. Return status insufficient_evidence, repeat exactly these source IDs, and give one concise limitation explaining why no substantive finding can be made.""" % ", ".join(SOURCES)


def main():
    try:
        load_dotenv(ROOT / ".env")
        with (ROOT / "config/model.toml").open("rb") as file:
            config = tomllib.load(file)
        if config != {"schema_version": 1, "model": "gemini-3.6-flash",
                      "prompt_version": "m0.5-evidence-metadata-v1", "max_output_tokens": 256,
                      "temperature": 0, "thinking_level": "minimal"}:
            raise ValueError("Unexpected M0.5 model configuration")
        client = GeminiClient(os.environ.get("GEMINI_API_KEY"))
        result, metadata = client.generate_structured(prompt(), config["model"], config["max_output_tokens"], config["temperature"])
        validated = validate_m0_output(result, "MSFT", SOURCES)
        output = {"schema_version": 1, "mode": "live_access_proof", "status": "success",
                  "prompt_version": config["prompt_version"], "result": validated, "metadata": metadata,
                  "limitations": ["Single structured-output call only; no tools, web search, document body or investment decision.",
                                  "Schema validity does not establish factual correctness.",
                                  "The model has no access to source passages in this proof."]}
    except ModelError as exc:
        output = {"mode": "live_access_proof", "status": exc.status, "error": str(exc),
                  "safe_diagnostics": exc.details}
    except (ValueError, KeyError, TypeError, OSError, tomllib.TOMLDecodeError) as exc:
        output = {"mode": "live_access_proof", "status": "failed_validation", "error": str(exc)}
    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())


