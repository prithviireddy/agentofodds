"""M1.2 return/covariance/optimiser tests."""
from datetime import date
from decimal import Decimal
import numpy as np
import unittest
from backend.app.contracts.market_data import DailyClose, timestamp
from backend.app.domain.numerical_inputs import PriceInput, NumericalInputError
from backend.app.domain.optimizer import solve_minimum_variance
from backend.app.domain.policy import InvestmentPolicy
from backend.app.domain.returns import aligned_simple_returns, sample_covariance

AS_OF = timestamp("2025-01-31T23:59:59Z")
HASH = "b" * 64


def policy(symbols=("AAA", "BBB"), **changes):
    values = dict(schema_version=1, policy_id="numerical-policy", as_of=AS_OF, symbols=symbols, capital=Decimal("10000"), currency="USD", objective="minimum_variance", min_asset_weight=Decimal("0"), max_asset_weight=Decimal("1"), min_cash_weight=Decimal("0"), max_cash_weight=Decimal("0"), review_frequency="monthly")
    values.update(changes)
    return InvestmentPolicy(**values)


def price_input(availability="verified"):
    bars = []
    values = {"AAA": (100, 110, 121), "BBB": (100, 105, 110.25)}
    for symbol, closes in values.items():
        for offset, close in enumerate(closes):
            session = date(2025, 1, 28 + offset)
            bars.append(DailyClose(symbol, session, Decimal(str(close)), timestamp(f"2025-01-{28 + offset}T22:00:00Z"), f"fixture:{symbol}:{session}"))
    return PriceInput(1, AS_OF, ("AAA", "BBB"), "fixture", "synthetic", "none", "USD", timestamp("2026-09-21T00:00:00Z"), HASH, availability, tuple(bars), (), "success")


class ReturnsTests(unittest.TestCase):
    def test_aligned_simple_returns_and_sample_covariance(self):
        returns = aligned_simple_returns(price_input())
        np.testing.assert_allclose(returns.values, [[0.1, 0.05], [0.1, 0.05]])
        np.testing.assert_allclose(sample_covariance(returns), [[0, 0], [0, 0]], atol=1e-16)

    def test_unverified_or_short_series_cannot_form_covariance(self):
        with self.assertRaises(NumericalInputError):
            aligned_simple_returns(price_input("not_verified"))
        source = price_input()
        short = PriceInput(**{**source.__dict__, "bars": source.bars[:4]})
        with self.assertRaises(NumericalInputError):
            aligned_simple_returns(short)


class OptimiserTests(unittest.TestCase):
    def test_known_diagonal_solution(self):
        result = solve_minimum_variance(policy(), [[1, 0], [0, 4]])
        self.assertEqual(result.status, "success")
        self.assertAlmostEqual(float(result.weights["AAA"]), 0.8, places=7)
        self.assertAlmostEqual(float(result.weights["BBB"]), 0.2, places=7)
        self.assertEqual(result.cash_weight, Decimal("0.0"))
        self.assertAlmostEqual(sum(map(float, result.weights.values())) + float(result.cash_weight), 1.0, places=10)

    def test_cash_bound_is_explicit_and_respected(self):
        result = solve_minimum_variance(policy(max_cash_weight=Decimal("0.1")), [[1, 0], [0, 4]])
        self.assertEqual(result.status, "success")
        self.assertAlmostEqual(float(result.weights["AAA"]), 0.72, places=7)
        self.assertAlmostEqual(float(result.weights["BBB"]), 0.18, places=7)
        self.assertEqual(result.cash_weight, Decimal("0.1"))

    def test_bounds_and_infeasible_policy_are_explicit(self):
        result = solve_minimum_variance(policy(max_asset_weight=Decimal("0.5")), [[1, 0], [0, 4]])
        self.assertAlmostEqual(float(result.weights["AAA"]), 0.5, places=8)
        self.assertAlmostEqual(float(result.weights["BBB"]), 0.5, places=8)
        impossible = policy(min_asset_weight=Decimal("0.6"))
        self.assertEqual(solve_minimum_variance(impossible, [[1, 0], [0, 4]]).status, "infeasible")

    def test_invalid_covariance_fails_without_weights(self):
        for matrix in ([[1, 2], [0, 1]], [[1, 2], [2, 1]], [[1, 0, 0], [0, 1, 0]]):
            with self.subTest(matrix=matrix):
                result = solve_minimum_variance(policy(), matrix)
                self.assertEqual(result.status, "failed_validation")
                self.assertEqual(result.weights, {})


if __name__ == "__main__":
    unittest.main()
