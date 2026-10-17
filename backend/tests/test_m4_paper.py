"""Opening ledger arithmetic, consent, identity and durable exactly-once approval."""
from copy import deepcopy
from contextlib import closing
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal as D
from http.client import HTTPConnection
from http.server import HTTPServer
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
import unittest

from backend.app.application.demo import DemoService
from backend.app.domain.paper import PaperError, opening_plan, reconcile
from backend.app.domain.policy import InvestmentPolicy
from backend.app.domain.optimizer import PortfolioResult
from backend.app.ui import handler


class ArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.cutoff = datetime(2025, 1, 31, 23, 59, tzinfo=timezone.utc)
        self.fill = datetime(2025, 2, 3, 21, tzinfo=timezone.utc)
        self.policy = InvestmentPolicy(1, 'paper-test', self.cutoff, ('AAA', 'BBB'), D('1000'),
            'USD', 'minimum_variance', D('0'), D('.8'), D('0'), D('.3'), 'manual')
        self.allocation = PortfolioResult('success', {'AAA': D('.4'), 'BBB': D('.4')}, D('.2'), 0, {})
        self.options = dict(execution_at=self.fill, fee_bps='10', corporate_actions=[],
            quotes={s: dict(price=p, at=self.fill.isoformat(), source_id='fixture:'+s)
                    for s, p in [('AAA', '3'), ('BBB', '7')]})

    def test_exact_fractional_shares_fees_and_replay(self):
        plan = opening_plan(self.policy, self.allocation, **self.options)
        self.assertEqual(plan['balances']['holdings']['AAA']['quantity'], '400/3')
        self.assertEqual(plan['balances']['cash'], '996/5')
        self.assertEqual(plan['balances']['fees'], '4/5')
        self.assertEqual(plan['balances']['equity_at_fill'], '4996/5')
        self.assertEqual(reconcile(plan['journal']), plan['balances'])

    def test_invalid_timing_prices_fees_and_actions(self):
        for patch in ({'execution_at': self.cutoff}, {'execution_at': self.cutoff.replace(tzinfo=None)},
                      {'quotes': {}}, {'fee_bps': '-1'}, {'fee_bps': 'NaN'}, {'fee_bps': True},
                      {'corporate_actions': [{'kind': 'split'}]}):
            with self.subTest(patch=patch), self.assertRaises(PaperError):
                opening_plan(self.policy, self.allocation, **{**self.options, **patch})
        for price in ('0', '-1', 'Infinity'):
            options = deepcopy(self.options)
            options['quotes']['AAA']['price'] = price
            with self.assertRaises(PaperError):
                opening_plan(self.policy, self.allocation, **options)

    def test_post_fee_bounds_are_not_relaxed(self):
        with self.assertRaises(PaperError) as error:
            opening_plan(replace(self.policy, min_cash_weight=D('.2')), self.allocation, **self.options)
        self.assertEqual(error.exception.status, 'infeasible_execution')

    def test_corrupt_duplicate_and_overdrawn_entries_fail(self):
        plan = opening_plan(self.policy, self.allocation, **self.options)
        for mutation in ('amount', 'duplicate', 'overdraw'):
            journal = deepcopy(plan['journal'])
            if mutation == 'amount':
                journal[1]['quantity'] = '1'
            elif mutation == 'duplicate':
                journal.append(journal[1])
            else:
                journal[0]['cash_delta'] = '1'
            with self.assertRaises(PaperError) as error:
                reconcile(journal)
            self.assertEqual(error.exception.status, 'failed_reconciliation')


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = DemoService(self.temp.name)

    def complete(self, scenario='normal'):
        run = self.service.create({**self.service.settings()['demo'], 'scenario': scenario})
        state = self.service.get(run['run_id'])
        for _ in range(30):
            if not state['can_continue']:
                return state
            state = self.service.advance(run['run_id'])
        self.fail('Workflow did not stop')

    def test_preview_consent_idempotency_reload_and_no_model_calls(self):
        state = self.complete()
        run_id = state['run_id']
        preview = self.service.paper.preview(run_id)
        self.assertFalse(self.service.paper.database.exists())
        for consent in (False, None, 1, 'true'):
            with self.assertRaises(PaperError):
                self.service.paper.approve(run_id, preview['proposal_id'], consent)
        receipt = self.service.paper.approve(run_id, preview['proposal_id'], True)
        self.assertEqual(receipt['summary']['reconciliation_difference'], '0')
        self.assertEqual(receipt['summary']['journal_entries'], 6)
        self.assertEqual(self.service.paper.approve(run_id, preview['proposal_id'], True), receipt)
        self.assertEqual(DemoService(self.temp.name).paper.get(run_id), receipt)
        self.assertEqual(self.service.get(run_id), state)
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM approvals').fetchone()[0], 1)
        with self.assertRaises(PaperError) as error:
            self.service.paper.approve(run_id, 'different', True)
        self.assertEqual(error.exception.status, 'approval_conflict')

    def test_changed_fill_invalidates_preview(self):
        state = self.complete()
        preview = self.service.paper.preview(state['run_id'])
        fill = json.loads(self.service.paper.fill_path.read_text())
        fill['prices']['MSFT'] = '103'
        path = Path(self.temp.name) / 'changed-fills.json'
        path.write_text(json.dumps(fill))
        self.service.paper.fill_path = path
        with self.assertRaises(PaperError) as error:
            self.service.paper.approve(state['run_id'], preview['proposal_id'], True)
        self.assertEqual(error.exception.status, 'proposal_changed')
        self.assertIsNone(self.service.paper.get(state['run_id']))

    def test_changed_policy_invalidates_approval(self):
        state = self.complete()
        preview = self.service.paper.preview(state['run_id'])
        path = Path(self.temp.name) / (state['run_id'] + '.input.json')
        manifest = json.loads(path.read_text())
        manifest['values']['capital'] = '20000'
        path.write_text(json.dumps(manifest))
        with self.assertRaises(PaperError) as error:
            self.service.paper.approve(state['run_id'], preview['proposal_id'], True)
        self.assertEqual(error.exception.status, 'proposal_changed')
        self.assertIsNone(self.service.paper.get(state['run_id']))

    def test_unreviewed_and_rejected_runs_cannot_be_approved(self):
        for state in (self.service.create(self.service.settings()['demo']), self.complete('review_rejected')):
            with self.assertRaises(PaperError) as error:
                self.service.paper.approve(state['run_id'], 'fake', True)
            self.assertEqual(error.exception.status, 'not_reviewed')

    def test_transaction_failure_leaves_no_approval_and_retry_succeeds(self):
        state = self.complete()
        preview = self.service.paper.preview(state['run_id'])
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute('CREATE TABLE approvals (run_id TEXT PRIMARY KEY, proposal_id TEXT UNIQUE, payload TEXT, sha256 TEXT)')
            connection.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON approvals BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.service.paper.approve(state['run_id'], preview['proposal_id'], True)
        self.assertIsNone(self.service.paper.get(state['run_id']))
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute('DROP TRIGGER fail_insert')
        self.assertEqual(self.service.paper.approve(state['run_id'], preview['proposal_id'], True)['status'], 'approved')

    def test_receipt_corruption_is_detected(self):
        state = self.complete()
        preview = self.service.paper.preview(state['run_id'])
        self.service.paper.approve(state['run_id'], preview['proposal_id'], True)
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute("UPDATE approvals SET sha256 = 'corrupt'")
        with self.assertRaises(PaperError) as error:
            self.service.paper.get(state['run_id'])
        self.assertEqual(error.exception.status, 'failed_reconciliation')

    def test_http_explicit_approval_and_reload(self):
        state = self.complete()
        server = HTTPServer(('127.0.0.1', 0), handler(self.service))
        Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def call(method, suffix, data=None):
            connection = HTTPConnection('127.0.0.1', server.server_port)
            connection.request(method, '/api/runs/' + state['run_id'] + suffix,
                body=json.dumps(data) if data is not None else None,
                headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
            connection.close()
            return result
        status, preview = call('GET', '/paper')
        self.assertEqual(status, 200)
        self.assertEqual(call('POST', '/approve-paper', {})[0], 409)
        body = {'approved': True, 'proposal_id': preview['proposal_id']}
        status, receipt = call('POST', '/approve-paper', body)
        self.assertEqual(status, 200)
        self.assertEqual(call('POST', '/approve-paper', body), (200, receipt))
        self.assertEqual(call('GET', '/paper'), (200, receipt))


if __name__ == '__main__':
    unittest.main()
