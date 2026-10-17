"""Manual numerical monitoring and immutable historical valuation replay."""
from contextlib import closing
from datetime import datetime, timezone
import json
import sqlite3

from backend.app.application.paper import digest
from backend.app.domain.paper import PaperError
from backend.app.domain.valuation import value_portfolio
from backend.app.workflows.checkpoint import canonical


class MonitoringService:
    def __init__(self, paper, provider):
        self.paper, self.provider = paper, provider

    def receipt(self, run_id):
        receipt = self.paper.get(run_id)
        if receipt is None:
            raise PaperError('approval_required', 'Approve the opening portfolio before valuation')
        return receipt

    def history(self, run_id):
        receipt = self.receipt(run_id)
        with closing(sqlite3.connect(self.paper.database)) as connection:
            if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='valuations'").fetchone():
                return []
            rows = connection.execute('SELECT payload, sha256 FROM valuations WHERE run_id=? ORDER BY valuation_at', (run_id,)).fetchall()
        snapshots = []
        for payload, checksum in rows:
            snapshot = json.loads(payload)
            if (digest(snapshot) != checksum or snapshot['run_id'] != run_id or
                    snapshot['proposal_id'] != receipt['proposal_id'] or
                    snapshot['result'] != value_portfolio(receipt['binding']['plan'], snapshot['inputs'])):
                raise PaperError('failed_reconciliation', 'Saved valuation identity or arithmetic is corrupt')
            snapshots.append(snapshot)
        return snapshots

    def get(self, run_id):
        receipt = self.receipt(run_id)
        binding = receipt['binding']
        cutoff = binding.get('research_as_of')
        if cutoff is None:  # Backward-compatible with M4.2 receipts; no guessed timestamps.
            state = self.paper.demo.store.load(run_id)
            cutoff = state['configuration']['investment']['as_of'].isoformat()
        try:
            dates, price_error = self.provider.dates(), None
        except (OSError, ValueError, KeyError, TypeError) as exc:
            dates, price_error = [], 'Valuation fixture unavailable or invalid; saved replay remains available.'
        return {'mode': 'synthetic_historical_replay', 'run_id': run_id,
                'run_created_at': binding.get('run_created_at'), 'research_as_of': cutoff,
                'fill_at': receipt['binding']['plan']['execution_at'], 'approved_at': receipt['approved_at'],
                'available_dates': dates, 'price_error': price_error, 'history': self.history(run_id),
                'limitations': ['Manual fixture valuation only; no live prices, fresh research or automatic monitoring.',
                    'Cash and shares remain unchanged. Returns include opening fees; dividends, taxes and liquidation costs are excluded.',
                    'Freshness is measured against the selected historical date, not today. No market-calendar validation.']}

    def update(self, run_id, at):
        with self.paper.demo.store.locked(run_id):
            receipt = self.receipt(run_id)
            existing = next((s for s in self.history(run_id) if s['inputs']['valuation_at'] == at), None)
            # Saved dates replay their archived inputs even if the fixture subsequently changes.
            if existing:
                return existing
            plan = receipt['binding']['plan']
            inputs = self.provider.prices(at, set(plan['balances']['holdings']))
            result = value_portfolio(plan, inputs)
            snapshot = {'run_id': run_id, 'proposal_id': receipt['proposal_id'],
                        'mode': 'synthetic_historical_replay', 'inputs': inputs, 'result': result,
                        'recorded_at': datetime.now(timezone.utc).isoformat()}
            with closing(sqlite3.connect(self.paper.database)) as connection, connection:
                connection.execute('BEGIN IMMEDIATE')
                connection.execute('CREATE TABLE IF NOT EXISTS valuations (run_id TEXT NOT NULL, valuation_at TEXT NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(run_id, valuation_at))')
                connection.execute('INSERT INTO valuations VALUES (?, ?, ?, ?)',
                                   (run_id, at, canonical(snapshot), digest(snapshot)))
            return snapshot
