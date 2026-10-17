"""Exact, provider-independent arithmetic for opening a synthetic paper portfolio."""
from datetime import datetime
from decimal import Decimal, localcontext
from fractions import Fraction


class PaperError(ValueError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def number(value):
    """Exact rational values; decimal rendering is for display only."""
    if isinstance(value, bool):
        raise ValueError("Boolean is not a ledger number")
    try:
        return Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError("Invalid finite ledger number") from exc


def display(value, places=2):
    value = number(value)
    with localcontext() as context:
        context.prec = 50
        return format(Decimal(value.numerator) / Decimal(value.denominator), f".{places}f")


def reconcile(journal):
    """Replay funding and purchases; reject inconsistent entries or negative cash."""
    cash = Fraction(0)
    capital = Fraction(0)
    fees = Fraction(0)
    holdings = {}
    ids = set()
    if not journal or journal[0].get("kind") != "funding":
        raise PaperError("failed_reconciliation", "Opening funding entry is required")
    try:
        for index, entry in enumerate(journal):
            if entry["entry_id"] in ids:
                raise ValueError("Duplicate journal entry")
            ids.add(entry["entry_id"])
            amount = number(entry["cash_delta"])
            if entry["kind"] == "funding":
                if index != 0 or amount <= 0:
                    raise ValueError("Only one positive opening funding entry is allowed")
                capital = amount
            elif entry["kind"] == "buy":
                symbol = entry["symbol"]
                quantity, price, fee = (number(entry[k]) for k in ("quantity", "price", "fee"))
                if quantity <= 0 or price <= 0 or fee < 0 or amount != -(quantity * price + fee):
                    raise ValueError("Trade arithmetic does not reconcile")
                prior = holdings.setdefault(symbol, {"quantity": Fraction(0), "cost": Fraction(0)})
                prior["quantity"] += quantity
                prior["cost"] += quantity * price
                fees += fee
            else:
                raise ValueError("Unsupported journal event")
            cash += amount
            if cash < 0:
                raise ValueError("Insufficient cash")
        value = sum((h["cost"] for h in holdings.values()), Fraction(0))
        if cash + value + fees != capital:
            raise ValueError("Cash, position costs and fees do not equal funded capital")
        return {"cash": str(cash), "capital": str(capital), "fees": str(fees), "position_cost": str(value),
                "holdings": {s: {k: str(v) for k, v in h.items()} for s, h in holdings.items()},
                "equity_at_fill": str(cash + value), "difference": "0"}
    except (ValueError, TypeError, KeyError) as exc:
        raise PaperError("failed_reconciliation", str(exc)) from exc


def opening_plan(policy, portfolio, *, execution_at, quotes, fee_bps, corporate_actions):
    """Buys only; exact fractional shares, explicit fees, no unapproved rebalancing."""
    try:
        policy.validate()
        if (not isinstance(execution_at, datetime) or execution_at.tzinfo is None or
                execution_at.utcoffset() is None or execution_at.date() <= policy.as_of.date()):
            raise ValueError("Synthetic fill must be on a session after the decision cutoff")
        if corporate_actions != []:
            raise PaperError("unsupported_corporate_action", "Splits and dividends are not supported by this opening ledger")
        if portfolio.status != "success" or set(portfolio.weights) != set(policy.symbols):
            raise ValueError("Successful allocation for the selected symbols is required")
        if set(quotes) != set(policy.symbols):
            raise PaperError("missing_fill_prices", "Fill-price coverage must exactly match the selected assets")
        capital = number(policy.capital)
        fee_rate = number(fee_bps) / 10000
        if not 0 <= fee_rate <= 1:
            raise ValueError("Fee basis points must be between 0 and 10,000")
        if abs(sum(map(number, portfolio.weights.values())) + number(portfolio.cash_weight) - 1) > Fraction(1, 10**9):
            raise ValueError("Allocation weights do not reconcile")
        journal = [{"entry_id": "funding", "kind": "funding", "cash_delta": str(capital)}]
        for symbol in policy.symbols:
            weight = number(portfolio.weights[symbol])
            if not number(policy.min_asset_weight) <= weight <= number(policy.max_asset_weight):
                raise PaperError("infeasible_execution", "Asset weight is outside the unchanged policy bounds")
            quote = quotes[symbol]
            price = number(quote["price"])
            if price <= 0 or quote["at"] != execution_at.isoformat() or not quote["source_id"]:
                raise ValueError("Invalid dated fill-price provenance")
            if weight == 0:
                continue
            notional = capital * weight
            fee = notional * fee_rate
            journal.append({"entry_id": "buy:" + symbol, "kind": "buy", "symbol": symbol,
                            "quantity": str(notional / price), "price": str(price), "fee": str(fee),
                            "cash_delta": str(-notional - fee), "execution_at": execution_at.isoformat(),
                            "source_id": quote["source_id"]})
        result = reconcile(journal)
        equity = number(result["equity_at_fill"])
        if equity <= 0:
            raise PaperError("infeasible_execution", "Fees exhaust portfolio equity")
        cash_weight = number(result["cash"]) / equity
        if not number(policy.min_cash_weight) <= cash_weight <= number(policy.max_cash_weight):
            raise PaperError("infeasible_execution", "Residual cash violates the unchanged cash bounds")
        for symbol in policy.symbols:
            cost = number(result["holdings"].get(symbol, {}).get("cost", "0"))
            if not number(policy.min_asset_weight) <= cost / equity <= number(policy.max_asset_weight):
                raise PaperError("infeasible_execution", "Post-fee position weight violates policy bounds")
        return {"journal": journal, "balances": result, "execution_at": execution_at.isoformat(),
                "fee_bps": str(number(fee_bps)), "conventions": {
                    "mode": "synthetic_historical_replay", "fill": "declared_later_fixture_close",
                    "quantity": "exact_fractional_shares", "money": "exact_rational_usd_display_rounding_only",
                    "slippage": "zero", "fees": "explicit_bps", "taxes": "excluded",
                    "dividends": "unsupported_reject", "splits": "unsupported_reject",
                    "funding": "one_isolated_portfolio_per_run", "rebalancing": "not_supported"}}
    except PaperError:
        raise
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        raise PaperError("failed_validation", str(exc)) from exc
