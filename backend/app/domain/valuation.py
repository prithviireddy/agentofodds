"""Exact mark-to-market calculations; no model or provider dependency."""
from datetime import timedelta
from fractions import Fraction

from backend.app.contracts.market_data import DailyClose, timestamp
from backend.app.domain.paper import PaperError, number, reconcile, display


def value_portfolio(plan, inputs):
    try:
        at = timestamp(inputs['valuation_at'])
        fill = timestamp(plan['execution_at'])
        age = inputs['max_price_age_days']
        if type(age) is not int or not 0 <= age <= 30:
            raise ValueError('Explicit price age must be between 0 and 30 calendar days')
        if at < fill:
            raise PaperError('invalid_valuation_time', 'Valuation precedes the opening fill')
        if inputs['currency'] != 'USD' or inputs['adjustment'] != 'none':
            raise PaperError('incompatible_prices', 'Require USD unadjusted prices for the unchanged share ledger')
        if inputs['corporate_actions'] != []:
            raise PaperError('unsupported_corporate_action', 'Splits and dividends require ledger support before valuation')
        balances = reconcile(plan['journal'])
        if balances != plan['balances']:
            raise PaperError('failed_reconciliation', 'Opening balances disagree with journal')
        prices = [DailyClose.from_dict(row) for row in inputs['prices']]
        symbols = [row.symbol for row in prices]
        if len(set(symbols)) != len(symbols) or set(symbols) != set(balances['holdings']):
            raise PaperError('missing_prices', 'Require exactly one price per held asset')
        positions = {}
        for price in prices:
            if price.session > at.date() or price.available_at > at:
                raise PaperError('future_prices', 'Price was not available at the valuation cutoff')
            if price.session < fill.date():
                raise PaperError('stale_prices', 'Price precedes the opening fill')
            if at.date() - price.session > timedelta(days=age):
                raise PaperError('stale_prices', 'Price exceeds the declared calendar-day age limit')
            holding = balances['holdings'][price.symbol]
            positions[price.symbol] = str(number(holding['quantity']) * number(price.close))
        market = sum(map(number, positions.values()), Fraction(0))
        cash, capital = number(balances['cash']), number(balances['capital'])
        equity = cash + market
        pnl = equity - capital  # Includes opening fees; no invented sale/liquidation cost.
        return {'cash': str(cash), 'positions': positions, 'market_value': str(market),
                'equity': str(equity), 'pnl_since_funding': str(pnl),
                'return_since_funding': str(pnl / capital), 'reconciliation_difference': '0',
                'summary': {'cash_usd': display(cash), 'equity_usd': display(equity),
                            'pnl_usd': display(pnl), 'return_percent': display(pnl / capital * 100),
                            'positions': {s: display(v) for s, v in positions.items()}}}
    except PaperError:
        raise
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        raise PaperError('failed_validation', str(exc)) from exc
