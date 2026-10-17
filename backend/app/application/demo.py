"""Local fixture application service. Does not import live provider adapters."""
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import uuid

from backend.app.contracts.market_data import DailyClose, timestamp
from backend.app.domain.policy import InvestmentPolicy
from backend.app.domain.selection import SelectionPolicy
from backend.app.domain.numerical_inputs import PriceInput
from backend.app.retrieval.index import EvidenceDocument, LocalEvidenceIndex
from backend.app.research.fundamental import ResearchRequest
from backend.app.workflows.runner import WorkflowBudget, run_workflow, RETRYABLE
from backend.app.workflows.checkpoint import JsonCheckpointStore, canonical
from backend.app.application.paper import PaperService
from backend.app.application.monitoring import MonitoringService
from backend.app.adapters.valuation_fixture import ValuationFixture

ROOT = Path(__file__).resolve().parents[3]


def plain(value):
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, (Decimal, datetime, date)):
        return str(value)
    return value


class FixtureFailure(Exception):
    status = "awaiting_quota"


class FixtureModel:
    def __init__(self, step, scenario, retry, quota_step):
        self.step, self.scenario, self.retry, self.quota_step = step, scenario, retry, quota_step

    def generate_json(self, prompt, schema, max_output_tokens, temperature):
        if self.scenario == "quota" and self.step == self.quota_step and not self.retry:
            raise FixtureFailure("Simulated quota failure; explicit retry is available.")
        if self.step.startswith("critic:"):
            rejected = self.scenario == "review_rejected"
            output = {"verdict": "rejected" if rejected else "approved", "target": "",
                      "rationale": "Scripted fixture review: " + ("evidence rejected." if rejected else "synthetic claims match the supplied text.")}
        else:
            citation = re.search(r"\[chunk_id=([a-f0-9]+)", prompt)
            if citation is None:
                raise ValueError("Fixture prompt lacks evidence")
            finding = {"claim": "Synthetic company revenue changed during the quarter.", "assessment": "neutral",
                       "citation_chunk_ids": [citation.group(1)]}
            if self.step.startswith("news:"):
                finding["interpretation"] = "The cause is unknown; no investment implication is established."
            output = {"company": self.step.split(":")[1], "status": "success", "findings": [finding],
                      "limitations": ["Scripted synthetic finding, not actual company research."]}
        return output, {"model": "fixture-ui-v1", "usage": {}}


class DemoService:
    def __init__(self, directory=None, fixture_path=None, fill_path=None, valuation_path=None, fixture_set="five"):
        if fixture_set not in ("five", "twenty"):
            raise ValueError("Unknown fixture profile")
        suffix = "_20" if fixture_set == "twenty" else ""
        self.fixture_set = fixture_set
        self.directory = Path(directory or ROOT / "data" / ("ui_runs" + suffix))
        self.store = JsonCheckpointStore(self.directory / "checkpoints")
        raw = Path(fixture_path or ROOT / "fixtures" / ("workflow_demo" + suffix + ".json")).read_bytes()
        self.fixture = json.loads(raw)
        self.fixture_hash = hashlib.sha256(raw).hexdigest()
        self.budget = WorkflowBudget(**self.fixture['budget']).validate() if 'budget' in self.fixture else WorkflowBudget(5, 15, 11520, 20, 1, 1, 0)
        companies = self.fixture['companies']
        if (not companies or len(companies) > self.budget.max_companies or
                len({c['symbol'] for c in companies}) != len(companies) or
                any(len(c['closes']) != len(self.fixture['sessions']) for c in companies)):
            raise ValueError("Invalid fixture universe or price-session coverage")
        self.paper = PaperService(self, fill_path or ROOT / "fixtures" / ("paper_fills" + suffix + ".json"))
        self.monitoring = MonitoringService(self.paper, ValuationFixture(valuation_path or ROOT / "fixtures" / ("paper_valuations" + suffix + ".json")))

    def settings(self):
        symbols = [c["symbol"] for c in self.fixture["companies"]]
        return {"companies": self.fixture["companies"], "as_of": self.fixture["as_of"], "fixture_set": self.fixture_set,
                "demo": {"capital": "10000", "symbols": symbols, "excluded_symbols": [], "min_asset_weight": "0",
                         "max_asset_weight": "0.5", "min_cash_weight": "0", "max_cash_weight": "0.1",
                         "review_frequency": "manual", "fundamental_assessments": ["neutral"], "news_assessments": ["neutral"],
                         "max_evidence_age_days": 30, "max_price_age_days": 1, "min_return_observations": 2,
                         "max_sample_volatility": 0.2, "min_candidates": 2, "scenario": "normal"},
                "budget": asdict(self.budget)}

    def inputs(self, values, retry=False):
        required = set(self.settings()["demo"])
        if not isinstance(values, dict) or set(values) != required:
            raise ValueError("All policy fields must be supplied; unexpected fields are rejected")
        available = {c["symbol"]: c for c in self.fixture["companies"]}
        symbols = tuple(values["symbols"])
        if not symbols or not set(symbols) <= set(available):
            raise ValueError("Choose companies from the configured fixture universe")
        if values["scenario"] not in ("normal", "missing_evidence", "quota", "review_rejected"):
            raise ValueError("Unknown fixture scenario")
        cutoff = timestamp(self.fixture["as_of"])
        investment = InvestmentPolicy(1, "ui-fixture-policy", cutoff, symbols, Decimal(values["capital"]), "USD", "minimum_variance",
            *(Decimal(values[key]) for key in ("min_asset_weight", "max_asset_weight", "min_cash_weight", "max_cash_weight")),
            values["review_frequency"]).validate()
        selection = SelectionPolicy("ui-fixture-selection", 1, tuple(values["excluded_symbols"]),
            tuple(values["fundamental_assessments"]), tuple(values["news_assessments"]),
            values["max_evidence_age_days"], values["max_price_age_days"], values["min_return_observations"],
            values["max_sample_volatility"], values["min_candidates"]).validate(symbols)
        bars = tuple(DailyClose(s, date.fromisoformat(day), Decimal(close), timestamp(day + "T22:00:00Z"), f"fixture:{s}:{day}")
                     for s in symbols for day, close in zip(self.fixture["sessions"], available[s]["closes"]))
        prices = PriceInput(1, cutoff, symbols, "fixture", "synthetic", "none", "USD", cutoff,
                            self.fixture_hash, "verified", bars, (), "success")
        text = self.fixture["evidence_text"]
        documents = [EvidenceDocument("fixture:" + s, s, "fixture", timestamp(self.fixture["published_at"]), cutoff,
                     "fixture://" + s, hashlib.sha256(text.encode()).hexdigest(), text) for s in symbols]
        if values["scenario"] == "missing_evidence":
            documents = [EvidenceDocument("fixture:OTHER", "OTHER", "fixture", cutoff, cutoff, "fixture://OTHER",
                          hashlib.sha256(text.encode()).hexdigest(), text)]
        return dict(investment=investment, selection_policy=selection, prices=prices, index=LocalEvidenceIndex.build(documents),
                    requests={s: ResearchRequest(s, cutoff, ("revenue",), 1) for s in symbols},
                    news_start=timestamp("2025-01-01T00:00:00Z"), budget=self.budget,
                    model_id="fixture-ui-v1", model_factory=lambda step: FixtureModel(step, values["scenario"], retry, "news:" + next((s for s in symbols if s not in selection.excluded_symbols), symbols[0])), store=self.store)

    def _manifest(self, run_id):
        self.store.path(run_id)  # Validate the identifier before building a filesystem path.
        path = self.directory / (run_id + ".input.json")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest["fixture_hash"] != self.fixture_hash:
            raise ValueError("Fixture changed; start a new run")
        return manifest

    def create(self, values):
        self.inputs(values)  # Reject invalid policy before persisting any run.
        run_id = uuid.uuid4().hex
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / (run_id + ".input.json")).open("x", encoding="utf-8") as handle:
            handle.write(canonical({"values": values, "fixture_hash": self.fixture_hash,
                                    "created_at": datetime.now(timezone.utc).isoformat()}))
        return {"run_id": run_id, "status": "created", "policy": values}

    def advance(self, run_id, retry=False):
        manifest = self._manifest(run_id)
        state = run_workflow(run_id, **self.inputs(manifest["values"], retry), retry_failed=retry, max_steps=1)
        return self.present(run_id, state, manifest["values"])

    def get(self, run_id):
        manifest = self._manifest(run_id)
        state = self.store.load(run_id)
        return self.present(run_id, state or {"status": "created"}, manifest["values"])

    def list_runs(self):
        return [self.get(p.name.removesuffix(".input.json")) for p in sorted(self.directory.glob("*.input.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:30]]

    def present(self, run_id, state, policy):
        results = state.get("results", {})
        success = state["status"] == "success"
        reports = {k: v for k, v in results.items() if k.startswith(("fundamental:", "news:"))}
        response = {"run_id": run_id, "status": state["status"], "reason": state.get("reason"), "mode": "synthetic_fixture",
                    "policy": policy, "as_of": self.fixture["as_of"], "progress": {"completed": state.get("cursor", 0),
                    "total": len(state.get("queue", []))}, "history": [{k: v for k, v in h.items() if k != "result"} for h in state.get("history", [])],
                    "can_continue": state["status"] in ("created", "checkpointed"),
                    "can_retry": state["status"] in RETRYABLE,
                    "reports": reports, "quantitative": results.get("quantitative"), "selection": results.get("selection"),
                    "allocation": results.get("allocation") if success else None,
                    "review": results.get("review"), "critic": results.get("critic:0"), "usage": state.get("usage"),
                    "budget": self.settings()["budget"], "fingerprint": state.get("fingerprint"),
                    "limitations": ["All prices, news, model findings and critic decisions are synthetic fixtures.",
                       "A reviewed fixture proposal is not investment advice, human approval or an executed trade."]}
        return plain(response)

