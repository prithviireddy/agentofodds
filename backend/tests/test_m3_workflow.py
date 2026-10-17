"""Offline integration, checkpoint recovery, budgets and review failures."""
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from backend.app.adapters.llm_gemini import ModelError
from backend.app.research.fundamental import ResearchRequest, run_fundamental_research
from backend.app.retrieval.index import LocalEvidenceIndex
from backend.app.workflows.checkpoint import JsonCheckpointStore
from backend.app.workflows.runner import WorkflowBudget, run_workflow
from backend.app.workflows.review import review_allocation
from backend.tests.test_m3_selection import inputs
from backend.tests.test_m1_numerical import price_input
from backend.tests.test_m2_research import corpus, moment, FakeModel, request


class FixtureModels:
    def __init__(self):
        self.calls = []
        self.fail_once = None
        self.crash_once = None
        self.critic_verdicts = []
        self.omit_usage = False

    def __call__(self, step):
        owner = self
        class Model:
            def generate_json(self, prompt, schema, max_output_tokens, temperature):
                owner.calls.append(step)
                if owner.crash_once == step:
                    owner.crash_once = None
                    raise KeyboardInterrupt("Simulated process interruption")
                if owner.fail_once == step:
                    owner.fail_once = None
                    raise ModelError("awaiting_quota", "Synthetic quota failure")
                if step.startswith("critic:"):
                    output = owner.critic_verdicts.pop(0) if owner.critic_verdicts else {
                        "verdict": "approved", "target": "", "rationale": "Fixture claims match the supplied passages."}
                else:
                    symbol = step.split(":")[1]
                    chunk = re.search(r"\[chunk_id=([a-f0-9]+)", prompt).group(1)
                    finding = {"claim": "Fixture revenue changed.", "assessment": "neutral", "citation_chunk_ids": [chunk]}
                    if step.startswith("news:"):
                        finding["interpretation"] = "Demand may have changed; this is uncertain."
                    output = {"company": symbol, "status": "success", "findings": [finding], "limitations": ["Synthetic fixture only."]}
                return output, {"model": "fixture-model", "usage": {} if owner.omit_usage else
                                {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15}}
        return Model()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = JsonCheckpointStore(self.temp.name)
        investment, selection, _, _, _ = inputs()
        prices = price_input()
        names = {"AAA": "MSFT", "BBB": "JPM"}
        prices = replace(prices, requested_symbols=investment.symbols,
                         bars=tuple(replace(b, symbol=names[b.symbol]) for b in prices.bars))
        # Short enough for complete review of both companies within the explicit prompt cap.
        index = LocalEvidenceIndex.build([replace(d, text=d.text[:150]) for d in corpus().documents])
        self.models = FixtureModels()
        self.kwargs = dict(investment=investment, selection_policy=selection, prices=prices, index=index,
            requests={s: ResearchRequest(s, investment.as_of, ("revenue",), 1) for s in investment.symbols},
            news_start=moment("2025-01-01T00:00:00"), budget=WorkflowBudget(5, 10, 7680, 20, 1, 2, 1),
            model_id="fixture-model", model_factory=self.models, store=self.store)

    def run_case(self, **changes):
        return run_workflow("fixture-run", **{**self.kwargs, **changes})

    def test_end_to_end_and_completed_resume_are_idempotent(self):
        state = self.run_case()
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["results"]["selection"].candidates, ("MSFT", "JPM"))
        portfolio = state["results"]["allocation"]
        self.assertAlmostEqual(float(sum(portfolio.weights.values()) + portfolio.cash_weight), 1)
        self.assertEqual(state["results"]["review"]["status"], "success")
        self.assertEqual(len(self.models.calls), 5)
        self.assertEqual(state["usage"]["reported_token_totals"]["totalTokenCount"], 75)
        self.assertEqual(self.run_case(), state)
        self.assertEqual(len(self.models.calls), 5)

    def test_midrun_resume_preserves_finished_roles(self):
        first = self.run_case(max_steps=2)
        self.assertEqual(first["status"], "checkpointed")
        self.assertEqual(len(self.models.calls), 1)
        final = self.run_case()
        self.assertEqual(final["status"], "success")
        self.assertEqual(self.models.calls.count("fundamental:MSFT"), 1)

    def test_quota_requires_explicit_retry_and_usage_remains_unknown(self):
        self.models.fail_once = "news:MSFT"
        failed = self.run_case()
        self.assertEqual(failed["status"], "awaiting_quota")
        self.assertEqual(len(self.models.calls), 2)
        self.assertEqual(self.run_case()["status"], "awaiting_quota")
        self.assertEqual(len(self.models.calls), 2)
        recovered = self.run_case(retry_failed=True)
        self.assertEqual(recovered["status"], "success")
        self.assertEqual(recovered["usage"]["model_calls_reserved"], 6)
        self.assertEqual(recovered["usage"]["calls_with_unknown_total_usage"], 1)
        self.assertEqual(self.models.calls.count("fundamental:MSFT"), 1)

    def test_retry_cap_survives_resume(self):
        self.models.fail_once = "fundamental:MSFT"
        self.run_case()
        self.models.fail_once = "fundamental:MSFT"
        self.assertEqual(self.run_case(retry_failed=True)["status"], "awaiting_quota")
        self.assertEqual(self.run_case(retry_failed=True)["status"], "retry_exhausted")
        self.assertEqual(len(self.models.calls), 2)

    def test_ambiguous_call_is_reserved_before_interruption(self):
        self.models.crash_once = "fundamental:MSFT"
        with self.assertRaises(KeyboardInterrupt):
            self.run_case()
        saved = self.store.load("fixture-run")
        self.assertEqual(saved["model_calls"], 1)
        self.assertEqual(saved["model_events"][0]["status"], "in_flight")
        self.assertEqual(self.run_case()["status"], "interrupted")
        recovered = self.run_case(retry_failed=True)
        self.assertEqual(recovered["status"], "success")
        self.assertEqual(recovered["model_calls"], 6)

    def test_budgets_stop_before_extra_dispatch(self):
        for field, value, expected_calls in (("max_model_calls", 1, 1), ("max_reserved_output_tokens", 768, 1),
                                              ("max_retrieval_queries", 1, 1)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                models = FixtureModels()
                state = self.run_case(budget=replace(self.kwargs["budget"], **{field: value}),
                                      model_factory=models, store=JsonCheckpointStore(folder))
                self.assertEqual(state["status"], "budget_exhausted")
                self.assertEqual(len(models.calls), expected_calls)

    def test_checkpoint_input_mismatch_and_corruption_make_no_calls(self):
        self.run_case(max_steps=1)
        changed = replace(self.kwargs["selection_policy"], max_price_age_days=2)
        self.assertEqual(self.run_case(selection_policy=changed)["status"], "checkpoint_mismatch")
        path = self.store.path("fixture-run")
        path.write_text('{"broken":true}', encoding="utf-8")
        self.assertEqual(self.run_case()["status"], "checkpoint_error")
        self.assertEqual(self.models.calls, [])

    def test_lock_and_invalid_run_id(self):
        with self.store.locked("fixture-run"):
            self.assertEqual(self.run_case()["status"], "checkpoint_error")
        self.assertEqual(run_workflow("../escape", **self.kwargs)["status"], "checkpoint_error")
        self.assertEqual(self.models.calls, [])

    def test_one_targeted_revision_then_second_review(self):
        self.models.critic_verdicts = [{"verdict": "revise", "target": "news:MSFT", "rationale": "State interpretation as uncertain."}]
        state = self.run_case()
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["revisions"], 1)
        self.assertEqual(self.models.calls.count("news:MSFT:revision1"), 1)
        self.assertEqual(len(self.models.calls), 7)
        self.assertEqual(state["results"]["critic:1"]["review"]["verdict"], "approved")

    def test_repeated_revision_and_unknown_target_fail_closed(self):
        self.models.critic_verdicts = [{"verdict": "revise", "target": "news:MSFT", "rationale": "Revise."}] * 2
        state = self.run_case()
        self.assertEqual(state["status"], "review_rejected")
        self.assertEqual(state["revisions"], 1)
        with tempfile.TemporaryDirectory() as folder:
            self.models.critic_verdicts = [{"verdict": "revise", "target": "shell:execute", "rationale": "Do something else."}]
            state = self.run_case(store=JsonCheckpointStore(folder))
            self.assertEqual(state["status"], "failed_validation")

    def test_review_overflow_is_explicit_and_not_truncated(self):
        index = LocalEvidenceIndex.build([replace(d, text=d.text * 8) for d in corpus().documents], chunk_words=20000)
        state = self.run_case(index=index)
        self.assertEqual(state["status"], "review_incomplete")
        self.assertNotIn("critic:0", self.models.calls)

    def test_missing_evidence_prevents_allocation_and_critic(self):
        index = LocalEvidenceIndex.build([replace(corpus().documents[0], symbol="XOM")])
        state = self.run_case(index=index)
        self.assertEqual(state["status"], "insufficient_candidates")
        self.assertNotIn("allocation", state["results"])
        self.assertEqual(self.models.calls, [])

    def test_bad_prices_stop_before_research(self):
        prices = self.kwargs["prices"]
        prices = replace(prices, availability_status="not_verified")
        self.assertEqual(self.run_case(prices=prices)["status"], "insufficient_evidence")
        self.assertEqual(self.models.calls, [])

    def test_unknown_usage_is_not_claimed_as_measured_zero(self):
        self.models.omit_usage = True
        state = self.run_case()
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["usage"]["calls_with_unknown_total_usage"], 5)
        self.assertIsNone(state["usage"]["cost"])

    def test_numeric_reviewer_rejects_unbalanced_portfolio(self):
        state = self.run_case()
        bad = replace(state["results"]["allocation"], cash_weight=Decimal("0.5"))
        result = review_allocation(self.kwargs["investment"], bad, state["results"]["allocation_statistics"].covariance)
        self.assertEqual(result["status"], "failed_validation")

    def test_five_company_fixture_workflow(self):
        symbols = ("MSFT", "JPM", "JNJ", "XOM", "WMT")
        investment = replace(self.kwargs["investment"], symbols=symbols)
        source = self.kwargs["prices"]
        base_bars = tuple(b for b in source.bars if b.symbol == "MSFT")
        prices = replace(source, requested_symbols=symbols,
                         bars=tuple(replace(b, symbol=s, source_id=f"fixture:{s}:{b.session}") for s in symbols for b in base_bars))
        template = corpus().documents[0]
        index = LocalEvidenceIndex.build([replace(template, source_id="fixture:" + s, symbol=s,
            text="Synthetic company revenue changed during the quarter; this fixture is not actual news.") for s in symbols])
        state = self.run_case(investment=investment, prices=prices, index=index,
            requests={s: ResearchRequest(s, investment.as_of, ("revenue",), 1) for s in symbols},
            budget=WorkflowBudget(5, 11, 8448, 10, 0, 1, 0))
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["results"]["selection"].candidates, symbols)
        self.assertEqual(tuple(state["results"]["allocation"].weights), symbols)
        self.assertEqual(len(self.models.calls), 11)

    def test_selected_subset_is_used_for_covariance_and_allocation(self):
        selection = replace(self.kwargs["selection_policy"], excluded_symbols=("MSFT",))
        state = self.run_case(selection_policy=selection)
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["results"]["allocation_statistics"].symbols, ("JPM",))
        self.assertEqual(tuple(state["results"]["allocation"].weights), ("JPM",))
        self.assertFalse(any("MSFT" in step for step in self.models.calls))

    def test_model_identity_mismatch_stops_the_workflow(self):
        state = self.run_case(model_id="another-model")
        self.assertEqual(state["status"], "failed_validation")
        self.assertEqual(len(self.models.calls), 1)
        self.assertNotIn("allocation", state["results"])

    def test_checkpoint_write_failure_prevents_dispatch(self):
        with patch.object(self.store, "save", side_effect=OSError("fixture disk failure")):
            self.assertEqual(self.run_case()["status"], "checkpoint_error")
        self.assertEqual(self.models.calls, [])

    def test_rejected_critic_without_revision_does_not_succeed(self):
        self.models.critic_verdicts = [{"verdict": "rejected", "target": "", "rationale": "Fixture evidence is not sufficient."}]
        state = self.run_case()
        self.assertEqual(state["status"], "review_rejected")
        self.assertEqual(state["revisions"], 0)
        self.assertEqual(len(self.models.calls), 5)

    def test_fundamental_cannot_cite_prompt_omitted_chunk(self):
        index = corpus()
        index = LocalEvidenceIndex(tuple(replace(c, text=c.text * 100) for c in index.chunks), index.documents)
        hits = index.search(request().queries[0], symbols=("MSFT",), top_k=2)
        model = FakeModel({"company": "MSFT", "status": "success", "findings": [{"claim": "Fixture.", "assessment": "neutral",
                           "citation_chunk_ids": [hits[1].chunk_id]}], "limitations": []})
        report = run_fundamental_research(index, request(), model)
        self.assertEqual(report.status, "failed_validation")
        self.assertEqual(len(report.evidence), 1)


if __name__ == "__main__":
    unittest.main()


