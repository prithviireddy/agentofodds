"""Candidate eligibility fixtures, with no network/model calls."""
from dataclasses import replace
from decimal import Decimal
import unittest
from backend.app.application.selection import select_candidates
from backend.app.domain.selection import SelectionPolicy
from backend.app.research.fundamental import FundamentalReport, ResearchFinding
from backend.app.research.news import NewsReport, NewsFinding
from backend.app.research.quantitative import run_quantitative_research
from backend.tests.test_m1_numerical import price_input, policy as investment_policy
from backend.tests.test_m2_research import corpus


def inputs():
    investment = investment_policy(symbols=("MSFT", "JPM"))
    rule = SelectionPolicy("fixture-rule", 1, (), ("positive", "neutral"), ("positive", "neutral"), 30, 1, 2, .2, 1)
    index = corpus()
    fundamentals, news = {}, {}
    for symbol in investment.symbols:
        hit = index.search("revenue", symbols=(symbol,), top_k=1)[0]
        refs = (hit.chunk_id,)
        fundamentals[symbol] = FundamentalReport("success", symbol, investment.as_of.isoformat(),
            (ResearchFinding("Fixture revenue changed.", "neutral", refs),), (hit,), ("Synthetic evidence.",), "fixture-v1", None, {})
        news[symbol] = NewsReport("success", symbol, investment.as_of.isoformat(), "2025-01-01T00:00:00+00:00",
            (NewsFinding("Fixture revenue changed.", "Demand could have changed.", "neutral", refs),), (hit,),
            ("Synthetic news.",), "fixture-v1", None, {})
    prices = price_input()
    names = {"AAA": "MSFT", "BBB": "JPM"}
    prices = replace(prices, requested_symbols=investment.symbols,
                     bars=tuple(replace(b, symbol=names[b.symbol]) for b in prices.bars))
    quant = run_quantitative_research(prices, max_age_days=1)
    return investment, rule, fundamentals, news, quant


class SelectionTests(unittest.TestCase):
    def test_success_is_deterministic_traceable_and_has_no_weights(self):
        args = inputs()
        result = select_candidates(*args)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.candidates, ("MSFT", "JPM"))
        self.assertEqual(result, select_candidates(*args))
        self.assertEqual(len(result.input_sha256), 64)
        self.assertEqual(result.policy_snapshot["selection"]["policy_id"], "fixture-rule")
        self.assertTrue(all(d.citation_chunk_ids and d.limitations for d in result.decisions))
        self.assertFalse(hasattr(result, "weights"))

    def test_exclusion_and_assessment_gate(self):
        investment, rule, fundamental, news, quant = inputs()
        result = select_candidates(investment, replace(rule, excluded_symbols=("JPM",)), fundamental, news, quant)
        self.assertEqual(result.candidates, ("MSFT",))
        self.assertIn("policy:explicit_exclusion", result.decisions[1].reasons)
        fundamental["MSFT"] = replace(fundamental["MSFT"], findings=(replace(fundamental["MSFT"].findings[0], assessment="negative"),))
        result = select_candidates(investment, rule, fundamental, news, quant)
        self.assertEqual(result.candidates, ("JPM",))
        self.assertIn("fundamental:assessment_excluded:negative", result.decisions[0].reasons)

    def test_missing_provider_failure_and_stale_reports_fail_closed(self):
        investment, rule, fundamental, news, quant = inputs()
        for status in ("awaiting_quota", "failed_validation", "service_unavailable", "insufficient_evidence"):
            changed = {**news, "MSFT": replace(news["MSFT"], status=status)}
            result = select_candidates(investment, rule, fundamental, changed, quant)
            self.assertEqual(result.candidates, ("JPM",))
            self.assertIn("news:" + status, result.decisions[0].reasons)
        result = select_candidates(investment, rule, {}, news, quant)
        self.assertEqual(result.status, "insufficient_candidates")
        for changed in (replace(rule, max_evidence_age_days=0), replace(rule, max_price_age_days=0),
                        replace(rule, min_return_observations=3)):
            self.assertEqual(select_candidates(investment, changed, fundamental, news, quant).status, "insufficient_candidates")

    def test_bad_citation_future_evidence_and_cutoff_mismatch(self):
        investment, rule, fundamental, news, quant = inputs()
        original = fundamental["MSFT"]
        invalid = [replace(original, findings=(replace(original.findings[0], citation_chunk_ids=("unknown",)),)),
                   replace(original, evidence=(replace(original.evidence[0], published_at="2025-02-01T00:00:00Z"),)),
                   replace(original, as_of="2025-01-30T23:59:59Z"), replace(original, symbol="JPM")]
        for report in invalid:
            result = select_candidates(investment, rule, {**fundamental, "MSFT": report}, news, quant)
            self.assertEqual(result.candidates, ("JPM",))
            self.assertIn("fundamental:failed_validation", result.decisions[0].reasons)

    def test_quantitative_limits_and_malformed_statistics(self):
        investment, rule, fundamental, news, quant = inputs()
        changed = replace(quant, statistics=replace(quant.statistics, sample_volatility=(.3, .1)))
        result = select_candidates(investment, rule, fundamental, news, changed)
        self.assertEqual(result.candidates, ("JPM",))
        self.assertIn("quantitative:volatility_limit", result.decisions[0].reasons)
        for bad in (None, replace(quant, status="stale_data"),
                    replace(quant, statistics=replace(quant.statistics, sample_volatility=(float("nan"), .1)))):
            self.assertEqual(select_candidates(investment, rule, fundamental, news, bad).status, "insufficient_candidates")

    def test_insufficient_count_and_infeasible_bounds_do_not_relax(self):
        investment, rule, fundamental, news, quant = inputs()
        changed = replace(rule, excluded_symbols=("JPM",), min_candidates=2)
        result = select_candidates(investment, changed, fundamental, news, quant)
        self.assertEqual(result.status, "insufficient_candidates")
        self.assertEqual(result.candidates, ())
        constrained = replace(investment, max_asset_weight=Decimal("0.6"))
        result = select_candidates(constrained, replace(changed, min_candidates=1), fundamental, news, quant)
        self.assertEqual(result.status, "infeasible")
        self.assertEqual(result.candidates, ())
        self.assertTrue(result.decisions[0].eligible)
        self.assertEqual(constrained.max_asset_weight, Decimal("0.6"))

    def test_invalid_policy_and_extra_company_are_structured(self):
        investment, rule, fundamental, news, quant = inputs()
        for bad in (replace(rule, max_sample_volatility=float("nan")), replace(rule, min_candidates=0),
                    replace(rule, excluded_symbols=("UNKNOWN",)), replace(rule, news_assessments=()),
                    replace(rule, max_price_age_days=True)):
            self.assertEqual(select_candidates(investment, bad, fundamental, news, quant).status, "failed_validation")
        self.assertEqual(select_candidates(investment, rule, {**fundamental, "OTHER": fundamental["MSFT"]}, news, quant).status,
                         "failed_validation")


if __name__ == "__main__":
    unittest.main()
