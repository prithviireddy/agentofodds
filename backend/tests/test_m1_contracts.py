"""M1.1 policy and numerical-input contract tests."""
from datetime import date
from decimal import Decimal
import unittest
from backend.app.config.universe import load_universe
from backend.app.contracts.market_data import DailyClose, timestamp
from backend.app.domain.numerical_inputs import NumericalInputError, PriceInput
from backend.app.domain.policy import InvestmentPolicy, PolicyError
from backend.app.sec_probe import ROOT


AS_OF = timestamp("2025-01-31T23:59:59Z")
SYMBOLS = ("MSFT", "JPM", "JNJ", "XOM", "WMT")
HASH = "a" * 64


def policy(**changes):
    values = dict(schema_version=1, policy_id="development-policy", as_of=AS_OF, symbols=SYMBOLS,
                  capital=Decimal("10000"), currency="USD", objective="minimum_variance",
                  min_asset_weight=Decimal("0"), max_asset_weight=Decimal("0.40"),
                  min_cash_weight=Decimal("0"), max_cash_weight=Decimal("0.10"), review_frequency="monthly")
    values.update(changes)
    return InvestmentPolicy(**values)


def prices(**changes):
    bars = tuple(DailyClose(symbol, date(2025, 1, 30), Decimal("100"), timestamp("2025-01-30T22:00:00Z"), f"fixture:{symbol}") for symbol in SYMBOLS)
    values = dict(schema_version=1, as_of=AS_OF, requested_symbols=SYMBOLS, provider="fixture", feed="synthetic-daily-close", adjustment="none", currency="USD", retrieved_at=timestamp("2026-09-21T00:00:00Z"), source_sha256=HASH, availability_status="verified", bars=bars, missing_symbols=(), status="success")
    values.update(changes)
    return PriceInput(**values)


class PolicyTests(unittest.TestCase):
    def test_explicit_feasible_policy(self):
        value = policy()
        self.assertIs(value.validate(), value)

    def test_no_implicit_policy_values(self):
        with self.assertRaises(TypeError):
            InvestmentPolicy()  # type: ignore[call-arg]

    def test_infeasible_bounds_are_rejected(self):
        for changes in ({"min_asset_weight": Decimal("0.25")}, {"max_asset_weight": Decimal("0.15"), "max_cash_weight": Decimal("0.10")}, {"min_cash_weight": Decimal("0.2"), "max_cash_weight": Decimal("0.1")}):
            with self.subTest(changes=changes):
                with self.assertRaises(PolicyError):
                    policy(**changes).validate()

    def test_currency_objective_and_cutoff_are_explicit(self):
        for changes in ({"currency": "INR"}, {"objective": "maximum_return"}, {"as_of": AS_OF.replace(tzinfo=None)}):
            with self.subTest(changes=changes):
                with self.assertRaises(PolicyError):
                    policy(**changes).validate()


class NumericalInputTests(unittest.TestCase):
    def test_complete_verified_data_is_eligible(self):
        value = prices().validate()
        self.assertTrue(value.point_in_time_eligible)

    def test_partial_data_and_unverified_availability_are_explicit(self):
        remaining = prices().bars[:-1]
        value = prices(bars=remaining, missing_symbols=("WMT",), status="partial_data", availability_status="not_verified").validate()
        self.assertFalse(value.point_in_time_eligible)

    def test_coverage_and_provenance_mismatches_are_rejected(self):
        for changes in ({"missing_symbols": ("MSFT",)}, {"status": "partial_data"}, {"provider": "unknown"}, {"source_sha256": "x"}):
            with self.subTest(changes=changes):
                with self.assertRaises(NumericalInputError):
                    prices(**changes).validate()

    def test_configured_universe_is_still_five_not_hardcoded_contract(self):
        universe = load_universe(ROOT / "config/universe.toml")
        self.assertEqual(universe.symbols, SYMBOLS)
        three = policy(symbols=("MSFT", "JPM", "JNJ"), max_asset_weight=Decimal("0.5"), max_cash_weight=Decimal("0.1"))
        self.assertIs(three.validate(), three)


if __name__ == "__main__":
    unittest.main()

