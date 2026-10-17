"""Exact valuation, cutoff safety, immutable replay and no-model boundary."""
from contextlib import closing
from copy import deepcopy
from http.client import HTTPConnection
from http.server import HTTPServer
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

from backend.app.application.demo import DemoService, FixtureModel
from backend.app.domain.paper import PaperError, reconcile
from backend.app.domain.valuation import value_portfolio
from backend.app.ui import handler


class ValuationTests(unittest.TestCase):
    def setUp(self):
        journal = [{'entry_id': 'fund', 'kind': 'funding', 'cash_delta': '100'},
                   {'entry_id': 'buy:A', 'kind': 'buy', 'symbol': 'A', 'quantity': '3/2',
                    'price': '40', 'fee': '1', 'cash_delta': '-61'}]
        self.plan = {'execution_at': '2025-02-03T21:00:00Z', 'journal': journal, 'balances': reconcile(journal)}
        self.inputs = {'valuation_at': '2025-02-04T22:00:00Z', 'max_price_age_days': 1,
                       'currency': 'USD', 'adjustment': 'none', 'corporate_actions': [],
                       'prices': [{'symbol': 'A', 'close': '42', 'session': '2025-02-04',
                                   'available_at': '2025-02-04T21:05:00Z', 'source_id': 'fixture:A'}]}

    def test_exact_valuation_includes_opening_fees_and_preserves_plan(self):
        before = deepcopy(self.plan)
        result = value_portfolio(self.plan, self.inputs)
        self.assertEqual(result['cash'], '39')
        self.assertEqual(result['positions'], {'A': '63'})
        self.assertEqual(result['equity'], '102')
        self.assertEqual(result['pnl_since_funding'], '2')
        self.assertEqual(result['return_since_funding'], '1/50')
        self.assertEqual(self.plan, before)

    def test_failure_outcomes(self):
        cases = [({'valuation_at': '2025-02-02T22:00:00Z'}, 'invalid_valuation_time'),
                 ({'valuation_at': '2025-02-10T22:00:00Z'}, 'stale_prices'),
                 ({'prices': []}, 'missing_prices'),
                 ({'prices': self.inputs['prices'] * 2}, 'missing_prices'),
                 ({'corporate_actions': [{'kind': 'dividend'}]}, 'unsupported_corporate_action'),
                 ({'adjustment': 'split'}, 'incompatible_prices'),
                 ({'currency': 'EUR'}, 'incompatible_prices'),
                 ({'max_price_age_days': True}, 'failed_validation')]
        for change, expected in cases:
            with self.subTest(change=change), self.assertRaises(PaperError) as error:
                value_portfolio(self.plan, {**self.inputs, **change})
            self.assertEqual(error.exception.status, expected)

    def test_future_prices_and_invalid_provenance(self):
        for change, expected in [({'available_at': '2025-02-05T00:00:00Z'}, 'future_prices'),
                                 ({'session': '2025-02-05', 'available_at': '2025-02-05T21:00:00Z'}, 'future_prices'),
                                 ({'source_id': ''}, 'failed_validation'),
                                 ({'close': 'NaN'}, 'failed_validation'),
                                 ({'close': '-1'}, 'failed_validation')]:
            inputs = deepcopy(self.inputs)
            inputs['prices'][0].update(change)
            with self.subTest(change=change), self.assertRaises(PaperError) as error:
                value_portfolio(self.plan, inputs)
            self.assertEqual(error.exception.status, expected)

    def test_corrupt_opening_balances_rejected(self):
        self.plan['balances']['cash'] = '100'
        with self.assertRaises(PaperError) as error:
            value_portfolio(self.plan, self.inputs)
        self.assertEqual(error.exception.status, 'failed_reconciliation')


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = DemoService(self.temp.name)
        state = self.service.create(self.service.settings()['demo'])
        self.run_id = state['run_id']
        for _ in range(30):
            state = self.service.get(self.run_id)
            if not state['can_continue']:
                break
            self.service.advance(self.run_id)
        self.assertEqual(state['status'], 'success')
        preview = self.service.paper.preview(self.run_id)
        self.receipt = self.service.paper.approve(self.run_id, preview['proposal_id'], True)
        self.at = self.service.monitoring.provider.dates()[0]

    def test_price_update_reload_and_replay_never_call_model_or_change_book(self):
        original = self.service.get(self.run_id)
        with patch.object(FixtureModel, 'generate_json', side_effect=AssertionError('Model called')), \
             patch.object(self.service, 'inputs', side_effect=AssertionError('Research constructed')):
            self.assertEqual(self.service.monitoring.get(self.run_id)['history'], [])
            first = self.service.monitoring.update(self.run_id, self.at)
            second_at = self.service.monitoring.provider.dates()[1]
            self.service.monitoring.update(self.run_id, second_at)
            self.assertEqual(self.service.monitoring.update(self.run_id, self.at), first)
            data = self.service.monitoring.get(self.run_id)
        self.assertEqual(len(data['history']), 2)
        self.assertTrue(data['run_created_at'])
        self.assertTrue(data['research_as_of'].startswith('2025-01-31'))
        self.assertEqual(data['approved_at'], self.receipt['approved_at'])
        self.assertEqual(DemoService(self.temp.name).monitoring.get(self.run_id), data)
        self.assertEqual(self.service.paper.get(self.run_id), self.receipt)
        self.assertEqual(self.service.get(self.run_id), original)

    def test_replay_survives_missing_provider_and_uses_archived_prices(self):
        saved = self.service.monitoring.update(self.run_id, self.at)
        self.service.monitoring.provider.path = Path(self.temp.name) / 'missing.json'
        self.assertEqual(self.service.monitoring.update(self.run_id, self.at), saved)
        data = self.service.monitoring.get(self.run_id)
        self.assertEqual(data['history'], [saved])
        self.assertEqual(data['available_dates'], [])
        self.assertTrue(data['price_error'])

    def test_failed_update_does_not_persist(self):
        with self.assertRaises(PaperError):
            self.service.monitoring.update(self.run_id, '2025-03-01T00:00:00Z')
        self.assertEqual(self.service.monitoring.history(self.run_id), [])
        inputs = self.service.monitoring.provider.prices(self.at, set(self.receipt['binding']['plan']['balances']['holdings']))
        inputs['prices'] = []
        with patch.object(self.service.monitoring.provider, 'prices', return_value=inputs):
            with self.assertRaises(PaperError):
                self.service.monitoring.update(self.run_id, self.at)
        self.assertEqual(self.service.monitoring.history(self.run_id), [])

    def test_storage_failure_rolls_back_and_retry_succeeds(self):
        self.service.monitoring.update(self.run_id, self.at)
        next_at = self.service.monitoring.provider.dates()[1]
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute("CREATE TRIGGER fail_valuation BEFORE INSERT ON valuations BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.service.monitoring.update(self.run_id, next_at)
        self.assertEqual(len(self.service.monitoring.history(self.run_id)), 1)
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute('DROP TRIGGER fail_valuation')
        self.service.monitoring.update(self.run_id, next_at)
        self.assertEqual(len(self.service.monitoring.history(self.run_id)), 2)

    def test_changed_provider_does_not_replace_saved_date(self):
        first = self.service.monitoring.update(self.run_id, self.at)
        with patch.object(self.service.monitoring.provider, 'prices', side_effect=AssertionError('Fetched prices during replay')):
            self.assertEqual(self.service.monitoring.update(self.run_id, self.at), first)

    def test_unapproved_run_refused(self):
        run = self.service.create(self.service.settings()['demo'])
        for method in (lambda: self.service.monitoring.get(run['run_id']),
                       lambda: self.service.monitoring.update(run['run_id'], self.at)):
            with self.assertRaises(PaperError) as error:
                method()
            self.assertEqual(error.exception.status, 'approval_required')

    def test_corrupt_saved_valuation_refused(self):
        self.service.monitoring.update(self.run_id, self.at)
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute("UPDATE valuations SET sha256='invalid'")
        with self.assertRaises(PaperError) as error:
            self.service.monitoring.get(self.run_id)
        self.assertEqual(error.exception.status, 'failed_reconciliation')

    def test_legacy_receipt_has_unknown_creation_date(self):
        from backend.app.application.paper import digest
        from backend.app.workflows.checkpoint import canonical
        receipt = deepcopy(self.receipt)
        del receipt['binding']['run_created_at']
        del receipt['binding']['research_as_of']
        receipt['proposal_id'] = digest(receipt['binding'])
        with closing(sqlite3.connect(self.service.paper.database)) as connection, connection:
            connection.execute('UPDATE approvals SET proposal_id=?, payload=?, sha256=?',
                               (receipt['proposal_id'], canonical(receipt), digest(receipt)))
        data = self.service.monitoring.get(self.run_id)
        self.assertIsNone(data['run_created_at'])
        self.assertTrue(data['research_as_of'].startswith('2025-01-31'))

    def test_http_dates_update_and_read_only_reload(self):
        server = HTTPServer(('127.0.0.1', 0), handler(self.service))
        Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def call(method, data=None):
            connection = HTTPConnection('127.0.0.1', server.server_port)
            connection.request(method, '/api/runs/' + self.run_id + '/valuations',
                body=json.dumps(data) if data is not None else None, headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
            connection.close()
            return result
        self.assertEqual(call('GET')[1]['history'], [])
        self.assertEqual(call('POST', {})[0], 400)
        status, snapshot = call('POST', {'valuation_at': self.at})
        self.assertEqual(status, 200)
        self.assertEqual(call('POST', {'valuation_at': self.at}), (200, snapshot))
        self.assertEqual(call('GET')[1]['history'], [snapshot])


if __name__ == '__main__':
    unittest.main()
