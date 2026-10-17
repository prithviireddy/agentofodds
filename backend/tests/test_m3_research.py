"""Synthetic M3.1 fixtures: no network, credentials, or model service."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import unittest
import numpy as np

from backend.app.adapters.llm_gemini import ModelError
from backend.app.research.news import NewsRequest, run_news_research
from backend.app.research.quantitative import run_quantitative_research
from backend.app.retrieval.index import LocalEvidenceIndex
from backend.tests.test_m2_research import corpus, request, moment, FakeModel
from backend.tests.test_m1_numerical import price_input


class NewsTests(unittest.TestCase):
    def setup_case(self):
        index = corpus()
        req = NewsRequest(request(), moment("2025-01-01T00:00:00"))
        hit = index.search(req.research.queries[0], symbols=("MSFT",), top_k=2)[0]
        output = {"company": "MSFT", "status": "success", "findings": [{
            "claim": "The fixture reports increased cloud revenue.",
            "interpretation": "This could suggest demand growth; the cause is uncertain.",
            "assessment": "positive", "citation_chunk_ids": [hit.chunk_id]}],
            "limitations": ["Synthetic event only."]}
        return index, req, output

    def test_separate_event_and_interpretation_with_dated_citation(self):
        index, req, output = self.setup_case()
        model = FakeModel(output)
        report = run_news_research(index, req, model)
        self.assertEqual(report.status, "success")
        self.assertEqual(model.calls, 1)
        self.assertIn("could", report.findings[0].interpretation)
        self.assertIn("cloud revenue increased", report.evidence[0].text)
        self.assertTrue(all(h.symbol == "MSFT" for h in report.evidence))
        self.assertEqual(report.model_metadata["model"], "fake")
        self.assertLessEqual(report.diagnostics["prompt_characters"], 8000)

    def test_window_company_and_filing_exclusions_skip_model(self):
        index, req, _ = self.setup_case()
        cases = [(index, replace(req, published_after=moment("2025-01-22T00:00:00"))),
                 (index, replace(req, research=request("XOM"))),
                 (index, replace(req, research=request(cutoff="2025-01-19T00:00:00"))),
                 (LocalEvidenceIndex.build([replace(d, source_type="sec_filing", url="https://example.test")
                                            for d in index.documents]), req)]
        for data, query in cases:
            with self.subTest(query=query):
                model = FakeModel()
                self.assertEqual(run_news_research(data, query, model).status, "insufficient_evidence")
                self.assertEqual(model.calls, 0)

    def test_invalid_window_and_output(self):
        index, req, output = self.setup_case()
        model = FakeModel()
        self.assertEqual(run_news_research(index, replace(req, published_after=req.research.as_of + timedelta(days=1)), model).status,
                         "failed_validation")
        self.assertEqual(model.calls, 0)
        for invalid in (None, {}, {**output, "company": "JPM"}):
            self.assertEqual(run_news_research(index, req, FakeModel(invalid)).status, "failed_validation")
        output["findings"][0]["citation_chunk_ids"] = ["invented"]
        self.assertEqual(run_news_research(index, req, FakeModel(output)).status, "failed_validation")

    def test_provider_failures_remain_structured(self):
        index, req, _ = self.setup_case()
        for status in ("awaiting_quota", "service_unavailable", "provider_error"):
            model = FakeModel(error=ModelError(status, "fixture failure"))
            self.assertEqual(run_news_research(index, req, model).status, status)
            self.assertEqual(model.calls, 1)

    def test_only_prompt_visible_chunks_can_be_cited(self):
        index, req, output = self.setup_case()
        chunks = tuple(replace(c, text=c.text * 100) for c in index.chunks)
        index = LocalEvidenceIndex(chunks, index.documents)
        rows = index.search(req.research.queries[0], symbols=("MSFT",), top_k=2)
        output["findings"][0]["citation_chunk_ids"] = [rows[1].chunk_id]
        report = run_news_research(index, req, FakeModel(output))
        self.assertEqual(report.status, "failed_validation")
        self.assertEqual(len(report.evidence), 1)
        self.assertLessEqual(report.diagnostics["prompt_characters"], 8000)


class QuantitativeTests(unittest.TestCase):
    def test_known_nonconstant_statistics_and_provenance(self):
        prices = price_input()
        bars = tuple(replace(b, close=Decimal("99")) if b.symbol == "AAA" and b.session.day == 30 else b
                     for b in prices.bars)
        report = run_quantitative_research(replace(prices, bars=bars), max_age_days=1)
        self.assertEqual(report.status, "success")
        np.testing.assert_allclose(report.statistics.mean_simple_return, [0, .05], atol=1e-15)
        np.testing.assert_allclose(report.statistics.sample_volatility, [np.sqrt(.02), 0], atol=1e-15)
        np.testing.assert_allclose(report.statistics.cumulative_return, [-.01, .1025])
        np.testing.assert_allclose(report.statistics.covariance, [[.02, 0], [0, 0]], atol=1e-15)
        self.assertEqual(report.statistics.observation_count, 2)
        self.assertEqual(report.provenance["source_sha256"], prices.source_sha256)
        self.assertFalse(report.diagnostics["model_called"])

    def test_stale_unverified_and_missing_prices(self):
        prices = price_input()
        self.assertEqual(run_quantitative_research(prices, max_age_days=0).status, "stale_data")
        self.assertEqual(run_quantitative_research(price_input("not_verified"), max_age_days=1).status, "insufficient_evidence")
        missing = replace(prices, bars=tuple(b for b in prices.bars if b.symbol == "AAA"),
                          missing_symbols=("BBB",), status="partial_data")
        self.assertEqual(run_quantitative_research(missing, max_age_days=1).status, "insufficient_evidence")

    def test_future_nonfinite_duplicate_and_short_inputs_fail(self):
        prices = price_input()
        bad_bars = [replace(prices.bars[0], available_at=prices.as_of + timedelta(seconds=1)),
                    replace(prices.bars[0], close=Decimal("NaN")),
                    replace(prices.bars[0], close=Decimal("Infinity")),
                    replace(prices.bars[0], available_at=prices.as_of.replace(tzinfo=None))]
        for bar in bad_bars:
            report = run_quantitative_research(replace(prices, bars=(bar,) + prices.bars[1:]), max_age_days=1)
            self.assertEqual(report.status, "failed_validation")
            self.assertIsNone(report.statistics)
        for bars in (prices.bars + prices.bars[:1], prices.bars[:2] + prices.bars[3:5]):
            self.assertEqual(run_quantitative_research(replace(prices, bars=bars), max_age_days=1).status, "failed_validation")

    def test_freshness_requires_explicit_valid_integer(self):
        for value in (-1, True, 1.5):
            self.assertEqual(run_quantitative_research(price_input(), max_age_days=value).status, "failed_validation")


if __name__ == "__main__":
    unittest.main()
