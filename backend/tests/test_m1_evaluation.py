"""M1.3 timing, cost, baseline and future-access tests."""
from datetime import date
from decimal import Decimal
import unittest

from backend.app.contracts.market_data import DailyClose, timestamp
from backend.app.domain.numerical_inputs import PriceInput
from backend.app.domain.optimizer import PortfolioResult
from backend.app.domain.policy import InvestmentPolicy
from backend.app.evaluation.basic import EvaluationPlan, compare_with_equal_weight, equal_weight_portfolio, evaluate_hold_period


DECISION = timestamp("2025-01-30T23:00:00Z")
HASH = "c" * 64


def policy(**changes):
    values = dict(schema_version=1, policy_id="evaluation-policy", as_of=DECISION, symbols=("AAA", "BBB"), capital=Decimal("10000"), currency="USD", objective="minimum_variance", min_asset_weight=Decimal("0"), max_asset_weight=Decimal("1"), min_cash_weight=Decimal("0"), max_cash_weight=Decimal("0"), review_frequency="monthly")
    values.update(changes)
    return InvestmentPolicy(**values)


def plan(**changes):
    values = dict(schema_version=1, decision_at=DECISION, execution_session=date(2025, 1, 31), valuation_session=date(2025, 2, 3), transaction_cost_bps=Decimal("0"), execution_convention="next_session_close", valuation_convention="close_to_close_total_value_excluding_dividends")
    values.update(changes)
    return EvaluationPlan(**values)


def prices(*, as_of="2025-02-03T23:00:00Z", late=False):
    rows = (("AAA", "2025-01-31", "100", "2025-01-31T22:00:00Z"), ("AAA", "2025-02-03", "110", "2025-02-03T22:00:00Z"), ("BBB", "2025-01-31", "100", "2025-01-31T22:00:00Z"), ("BBB", "2025-02-03", "90", "2025-02-04T01:00:00Z" if late else "2025-02-03T22:00:00Z"))
    bars = tuple(DailyClose(symbol, date.fromisoformat(session), Decimal(close), timestamp(available), f"fixture:{symbol}:{session}") for symbol, session, close, available in rows)
    return PriceInput(1, timestamp(as_of), ("AAA", "BBB"), "fixture", "synthetic", "none", "USD", timestamp("2026-09-21T00:00:00Z"), HASH, "verified", bars, (), "success")


class BasicEvaluationTests(unittest.TestCase):
    def test_equal_weight_uses_same_cash_and_bounds(self):
        result = equal_weight_portfolio(policy(max_cash_weight=Decimal("0.10")))
        self.assertEqual(result.weights, {"AAA": Decimal("0.45"), "BBB": Decimal("0.45")})
        self.assertEqual(result.cash_weight, Decimal("0.10"))

    def test_hold_period_return_and_explicit_cost(self):
        portfolio = PortfolioResult("success", {"AAA": Decimal("0.75"), "BBB": Decimal("0.25")}, Decimal("0"), None, {})
        result = evaluate_hold_period("test", portfolio, policy(), prices(), plan(transaction_cost_bps=Decimal("10")))
        self.assertEqual(result.status, "success")
        self.assertEqual(result.gross_return, Decimal("0.050"))
        self.assertEqual(result.transaction_cost, Decimal("0.001"))
        self.assertEqual(result.net_return, Decimal("0.049"))

    def test_comparison_uses_identical_dates_and_costs(self):
        optimized = PortfolioResult("success", {"AAA": Decimal("0.75"), "BBB": Decimal("0.25")}, Decimal("0"), None, {})
        result = compare_with_equal_weight(optimized, policy(), prices(), plan(transaction_cost_bps=Decimal("10")))
        self.assertEqual(result.equal_weight.net_return, Decimal("-0.001"))
        self.assertEqual(result.net_return_difference, Decimal("0.050"))

    def test_same_day_execution_is_rejected(self):
        portfolio = equal_weight_portfolio(policy())
        result = evaluate_hold_period("equal_weight", portfolio, policy(), prices(), plan(execution_session=date(2025, 1, 30)))
        self.assertEqual(result.status, "failed_validation")
        self.assertIn("after the decision", result.diagnostics["reason"])

    def test_late_price_and_early_evaluation_cutoff_are_rejected(self):
        portfolio = equal_weight_portfolio(policy())
        late = evaluate_hold_period("equal_weight", portfolio, policy(), prices(late=True), plan())
        early = evaluate_hold_period("equal_weight", portfolio, policy(), prices(as_of="2025-02-02T23:00:00Z"), plan())
        self.assertEqual(late.status, "failed_validation")
        self.assertEqual(early.status, "failed_validation")

    def test_policy_and_decision_cutoffs_must_match(self):
        mismatched = plan(decision_at=timestamp("2025-01-29T23:00:00Z"))
        result = evaluate_hold_period("equal_weight", equal_weight_portfolio(policy()), policy(), prices(), mismatched)
        self.assertEqual(result.status, "failed_validation")
        self.assertIn("Policy cutoff", result.diagnostics["reason"])


if __name__ == "__main__":
    unittest.main()
