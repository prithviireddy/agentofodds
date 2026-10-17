"""Bounded Gemini structured-output client for the M0.5 access proof."""
from datetime import datetime, timezone
import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

MODEL = "gemini-3.6-flash"
BASE = "https://generativelanguage.googleapis.com/v1beta/models/"


class ModelError(Exception):
    def __init__(self, status, message, details=None):
        super().__init__(message)
        self.status = status
        self.details = details or {}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _safe_response_details(payload, raw):
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    candidates = candidates if isinstance(candidates, list) else []
    finish_reasons = [candidate.get("finishReason") for candidate in candidates if isinstance(candidate, dict)]
    part_keys = []
    has_text = False
    for candidate in candidates:
        content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
        parts = content.get("parts", []) if isinstance(content, dict) else []
        for part in parts if isinstance(parts, list) else []:
            if isinstance(part, dict):
                part_keys.append(sorted(part.keys()))
                has_text = has_text or isinstance(part.get("text"), str)
    usage = payload.get("usageMetadata", {}) if isinstance(payload, dict) else {}
    safe_usage = {key: usage.get(key) for key in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")}
    return {"response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
            "candidate_count": len(candidates), "finish_reasons": finish_reasons,
            "part_keys": part_keys, "has_text": has_text, "usage": safe_usage}


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "status": {"type": "string", "enum": ["insufficient_evidence"]},
        "source_ids": {"type": "array", "items": {"type": "string"}},
        "limitation": {"type": "string"},
    },
    "required": ["company", "status", "source_ids", "limitation"],
    "additionalProperties": False,
}


class GeminiClient:
    """One non-tool model request per explicit access proof; no fallback or retry."""
    def __init__(self, api_key, opener=None):
        if not api_key:
            raise ModelError("missing_configuration", "Set GEMINI_API_KEY")
        if "\r" in api_key or "\n" in api_key:
            raise ModelError("failed_validation", "Gemini API key contains an invalid newline")
        self.api_key = api_key
        self.opener = opener or build_opener(NoRedirect()).open
        self.request_count = 0

    def generate_structured(self, prompt, model=MODEL, max_output_tokens=256, temperature=0):
        if model != MODEL:
            raise ValueError("Model is not allowlisted")
        if max_output_tokens != 256 or temperature != 0:
            raise ValueError("M0.5 budget settings are fixed")
        return self.generate_json(prompt, OUTPUT_SCHEMA, model=model,
                                  max_output_tokens=max_output_tokens, temperature=temperature)

    def generate_json(self, prompt, output_schema, model=MODEL, max_output_tokens=768, temperature=0,
                      thinking_level="minimal"):
        """One bounded JSON-schema request for an application role."""
        if model != MODEL:
            raise ValueError("Model is not allowlisted")
        if not isinstance(prompt, str) or not prompt or len(prompt) > 8_000:
            raise ValueError("Prompt must be nonempty and at most 8,000 characters")
        if not isinstance(output_schema, dict) or output_schema.get("type") != "object":
            raise ValueError("Output schema must describe an object")
        if not isinstance(max_output_tokens, int) or max_output_tokens < 1 or max_output_tokens > 1_024 or temperature != 0:
            raise ValueError("Model budget is outside the allowed range")
        if thinking_level != "minimal":
            raise ValueError("Thinking level must be minimal")
        if self.request_count >= 1:
            raise ModelError("awaiting_quota", "One model request per proof run")
        self.request_count += 1
        body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                           "generationConfig": {"temperature": temperature,
                                                "maxOutputTokens": max_output_tokens,
                                                "thinkingConfig": {"thinkingLevel": thinking_level},
                                                "responseMimeType": "application/json",
                                                "responseJsonSchema": output_schema}}).encode("utf-8")
        url = f"{BASE}{model}:generateContent"
        request = Request(url, data=body, method="POST", headers={"x-goog-api-key": self.api_key,
                                                                     "Content-Type": "application/json"})
        try:
            with self.opener(request, timeout=30) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ModelError("failed_validation", "Model response exceeds 2 MB limit")
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeError):
                details = {"stage": "response_json", "response_bytes": len(raw),
                           "response_sha256": hashlib.sha256(raw).hexdigest()}
                raise ModelError("failed_validation", "Gemini response envelope is not valid JSON", details) from None
            details = _safe_response_details(payload, raw)
            try:
                parts = payload["candidates"][0]["content"]["parts"]
                text = "".join(part["text"] for part in parts
                               if isinstance(part, dict) and isinstance(part.get("text"), str))
            except (KeyError, IndexError, TypeError):
                raise ModelError("failed_validation", "Gemini response has no readable candidate",
                                 {**details, "stage": "candidate"}) from None
            if not text:
                raise ModelError("failed_validation", "Gemini candidate contains no text",
                                 {**details, "stage": "candidate_text"})
            try:
                result = json.loads(text)
            except (ValueError, UnicodeError):
                raise ModelError("failed_validation", "Gemini candidate text is not valid JSON",
                                 {**details, "stage": "candidate_json",
                                  "candidate_text_characters": len(text)}) from None
            if not isinstance(result, dict):
                raise ModelError("failed_validation", "Gemini candidate JSON is not an object",
                                 {**details, "stage": "candidate_object"})
            return result, {"model": model, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                            "response_sha256": hashlib.sha256(raw).hexdigest(), "usage": details["usage"],
                            "thinking_level": thinking_level,
                            "retrieved_at": datetime.now(timezone.utc).isoformat()}
        except HTTPError as exc:
            status = "awaiting_quota" if exc.code == 429 else "service_unavailable" if exc.code == 503 else "provider_error"
            raise ModelError(status, f"Gemini HTTP {exc.code}; no automatic retry") from None
        except (URLError, TimeoutError, OSError):
            raise ModelError("provider_error", "Gemini transport failed; no automatic retry") from None


def validate_m0_output(result, company, source_ids):
    if set(result) != {"company", "status", "source_ids", "limitation"}:
        raise ValueError("Output keys do not match M0.5 schema")
    if result["company"] != company or result["status"] != "insufficient_evidence":
        raise ValueError("Output company or status is invalid")
    if not isinstance(result["source_ids"], list) or set(result["source_ids"]) != set(source_ids):
        raise ValueError("Output source IDs do not exactly match supplied evidence")
    if not isinstance(result["limitation"], str) or not result["limitation"].strip():
        raise ValueError("Output limitation is invalid")
    return result



