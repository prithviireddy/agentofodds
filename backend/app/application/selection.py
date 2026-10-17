"""Deterministic eligibility gates over specialist reports; no allocation or calls."""
from dataclasses import asdict, dataclass, replace
from datetime import date
import hashlib
import json
import math
import re

from backend.app.contracts.market_data import timestamp
from backend.app.domain.policy import PolicyError


@dataclass(frozen=True)
class CandidateDecision:
    symbol: str
    eligible: bool
    reasons: tuple[str, ...]
    citation_chunk_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class SelectionResult:
    status: str
    candidates: tuple[str, ...]
    decisions: tuple[CandidateDecision, ...]
    policy_snapshot: dict
    input_sha256: str
    limitations: tuple[str, ...]


def _research_reasons(report, role, symbol, cutoff, allowed, max_age):
    if report is None:
        return [f"{role}:missing_report"], (), ()
    reasons = []
    citations = []
    try:
        if report.symbol != symbol or timestamp(report.as_of) != cutoff:
            raise ValueError("identity_or_cutoff")
        if report.status != "success":
            return [f"{role}:{report.status}"], (), tuple(report.limitations)
        if not report.findings:
            raise ValueError("empty_findings")
        hits = {h.chunk_id: h for h in report.evidence}
        if len(hits) != len(report.evidence):
            raise ValueError("duplicate_evidence")
        start = timestamp(report.published_after) if role == "news" else None
        if start is not None and start > cutoff:
            raise ValueError("invalid_window")
        for finding in report.findings:
            if not finding.claim.strip() or not finding.citation_chunk_ids:
                raise ValueError("empty_finding")
            if finding.assessment not in {"positive", "negative", "mixed", "neutral"}:
                raise ValueError("invalid_assessment")
            if finding.assessment not in allowed:
                reasons.append(f"{role}:assessment_excluded:{finding.assessment}")
            if role == "news" and not finding.interpretation.strip():
                raise ValueError("empty_interpretation")
            if len(set(finding.citation_chunk_ids)) != len(finding.citation_chunk_ids):
                raise ValueError("duplicate_citation")
            for citation in finding.citation_chunk_ids:
                hit = hits[citation]
                published = timestamp(hit.published_at)
                if (hit.symbol != symbol or published > cutoff or (start is not None and published < start)
                        or not hit.text.strip() or not hit.source_id or not re.fullmatch(r"[0-9a-f]{64}", hit.source_sha256)):
                    raise ValueError("invalid_evidence")
                if (cutoff.date() - published.date()).days > max_age:
                    reasons.append(f"{role}:stale_evidence")
                citations.append(citation)
    except (ValueError, TypeError, KeyError, AttributeError):
        reasons.append(f"{role}:failed_validation")
    return reasons, tuple(dict.fromkeys(citations)), tuple(report.limitations)


def _quant_reasons(report, symbol, cutoff, policy):
    if report is None:
        return ["quantitative:missing_report"]
    try:
        if timestamp(report.as_of) != cutoff or symbol not in report.symbols:
            raise ValueError("identity_or_cutoff")
        if report.status != "success":
            return [f"quantitative:{report.status}"]
        stats = report.statistics
        if stats is None or stats.symbols != report.symbols or len(set(stats.symbols)) != len(stats.symbols):
            raise ValueError("invalid_statistics")
        n = len(stats.symbols)
        sessions = tuple(date.fromisoformat(s) for s in stats.return_sessions)
        if (len(sessions) != stats.observation_count or len(sessions) < 2 or tuple(sorted(set(sessions))) != sessions
                or sessions[-1] > cutoff.date()):
            raise ValueError("invalid_sessions")
        for values in (stats.mean_simple_return, stats.sample_volatility, stats.cumulative_return):
            if len(values) != n or any(not math.isfinite(v) for v in values):
                raise ValueError("invalid_values")
        if any(v < 0 for v in stats.sample_volatility):
            raise ValueError("negative_volatility")
        if report.provenance.get("availability_status") != "verified" or not re.fullmatch(r"[0-9a-f]{64}", report.provenance.get("source_sha256", "")):
            raise ValueError("invalid_provenance")
        if not report.provenance.get("source_ids") or report.provenance.get("calculation_version") != "price-statistics-v1":
            raise ValueError("missing_provenance")
        reasons = []
        if (cutoff.date() - sessions[-1]).days > policy.max_price_age_days:
            reasons.append("quantitative:stale_data")
        if stats.observation_count < policy.min_return_observations:
            reasons.append("quantitative:insufficient_observations")
        if stats.sample_volatility[stats.symbols.index(symbol)] > policy.max_sample_volatility:
            reasons.append("quantitative:volatility_limit")
        return reasons
    except (ValueError, TypeError, AttributeError, IndexError):
        return ["quantitative:failed_validation"]


def select_candidates(investment, policy, fundamentals, news, quantitative):
    """Require both text roles and computed statistics; retain all passing assets."""
    snapshot = {}
    digest = ""
    limits = ("Eligibility is not investment merit; citation validation does not establish factual correctness.",
              "No ranking, allocation, constraint relaxation or model call is performed.",
              "Volatility is an unannualised fraction per observed interval; calendar gaps remain unvalidated.")
    try:
        investment.validate()
        policy.validate(investment.symbols)
        snapshot = {"selection": asdict(policy), "investment": asdict(investment)}
        if not set(fundamentals) <= set(investment.symbols) or not set(news) <= set(investment.symbols):
            raise ValueError("Unexpected company report keys")
        payload = {"policy": snapshot, "fundamentals": {k: asdict(v) for k, v in fundamentals.items()},
                   "news": {k: asdict(v) for k, v in news.items()},
                   "quantitative": asdict(quantitative) if quantitative is not None else None}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    except (ValueError, TypeError, AttributeError) as exc:
        return SelectionResult("failed_validation", (), (), snapshot, digest, limits + (str(exc),))
    decisions = []
    for symbol in investment.symbols:
        reasons, citations, role_limits = [], [], []
        if symbol in policy.excluded_symbols:
            reasons.append("policy:explicit_exclusion")
        else:
            for role, reports, allowed in (("fundamental", fundamentals, policy.fundamental_assessments),
                                            ("news", news, policy.news_assessments)):
                why, refs, warnings = _research_reasons(reports.get(symbol), role, symbol, investment.as_of,
                                                       allowed, policy.max_evidence_age_days)
                reasons.extend(why)
                citations.extend(refs)
                role_limits.extend(warnings)
            reasons.extend(_quant_reasons(quantitative, symbol, investment.as_of, policy))
            if quantitative is not None:
                role_limits.extend(quantitative.limitations)
        decisions.append(CandidateDecision(symbol, not reasons, tuple(dict.fromkeys(reasons)) or ("eligible:all_gates_passed",),
                                            tuple(dict.fromkeys(citations)), tuple(dict.fromkeys(role_limits))))
    candidates = tuple(d.symbol for d in decisions if d.eligible)
    if len(candidates) < policy.min_candidates:
        return SelectionResult("insufficient_candidates", (), tuple(decisions), snapshot, digest,
                               limits + ("Eligible count is below the explicit minimum; no actionable candidate set.",))
    try:
        replace(investment, symbols=candidates).validate()
    except PolicyError as exc:
        return SelectionResult("infeasible", (), tuple(decisions), snapshot, digest, limits + (str(exc),))
    return SelectionResult("success", candidates, tuple(decisions), snapshot, digest, limits)
