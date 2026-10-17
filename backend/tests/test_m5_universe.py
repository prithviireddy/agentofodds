"""Twenty-company coverage, bounded review and numerical scaling regression."""
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

from backend.app.application.demo import DemoService
from backend.app.domain.optimizer import solve_minimum_variance
from backend.app.workflows.review import critic_prompt
from backend.app.workflows.runner import WorkflowBudget
from backend.app.universe_audit import audit
from backend.tests.test_m1_numerical import policy


class UniverseTests(unittest.TestCase):
    def test_twenty_company_audit_complete_and_usage_honest(self):
        result = audit('twenty')
        self.assertEqual(result['workflow_status'], 'success')
        self.assertEqual(result['paper_status'], 'success')
        self.assertEqual(result['saved_valuations'], 2)
        self.assertEqual(result['report_count'], 40)
        self.assertEqual(result['candidate_count'], 20)
        self.assertEqual(result['usage']['model_calls_reserved'], 41)
        self.assertEqual(result['usage']['calls_with_unknown_total_usage'], 41)
        self.assertIsNone(result['usage']['cost'])
        self.assertGreater(result['workflow_seconds'], 0)
        self.assertGreater(result['critic_prompt_characters'][0], 8000)
        self.assertLessEqual(result['critic_prompt_characters'][0], 64000)
        self.assertEqual(len(result['coverage']), 20)
        for row in result['coverage']:
            self.assertEqual(row['price_sessions'], 3)
            self.assertTrue(row['opening_fill'])
            self.assertEqual(row['valuation_frames'], 2)
            self.assertEqual(row['live_coverage'], 'not_audited')
            self.assertEqual({r['status'] for r in row['research'].values()}, {'success'})

    def test_default_five_profile_and_storage_remain_separate(self):
        five, twenty = DemoService(), DemoService(fixture_set='twenty')
        self.assertEqual(len(five.settings()['companies']), 5)
        self.assertEqual(len(twenty.settings()['companies']), 20)
        self.assertNotEqual(five.directory, twenty.directory)
        self.assertEqual(five.budget.max_critic_prompt_characters, 8000)
        self.assertEqual(twenty.budget.max_critic_prompt_characters, 64000)
        with self.assertRaises(ValueError):
            DemoService(fixture_set='live')

    def test_custom_subset_exclusions_and_full_critic_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            service = DemoService(directory, fixture_set='twenty')
            values = service.settings()['demo']
            values['symbols'] = values['symbols'][:9]
            values['excluded_symbols'] = ['JNJ']
            state = service.create(values)
            for _ in range(30):
                state = service.get(state['run_id'])
                if not state['can_continue']:
                    break
                service.advance(state['run_id'])
            self.assertEqual(state['status'], 'success')
            self.assertEqual(len(state['reports']), 16)
            self.assertNotIn('JNJ', state['allocation']['weights'])
            saved = service.store.load(state['run_id'])
            reports = {k: v for k,v in saved['results'].items() if k.startswith(('fundamental:', 'news:'))}
            prompt = critic_prompt(reports, max_characters=64000)
            for target, report in reports.items():
                self.assertIn(target, prompt)
                for finding in report.findings:
                    for citation in finding.citation_chunk_ids:
                        self.assertIn(citation, prompt)
            with self.assertRaises(ValueError):
                critic_prompt(reports, max_characters=8000)

    def test_incomplete_price_arrays_and_duplicate_universe_rejected(self):
        fixture = DemoService(fixture_set='twenty').fixture
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            fixture['companies'][0]['closes'].pop()
            path.write_text(json.dumps(fixture))
            with self.assertRaises(ValueError):
                DemoService(directory, fixture_path=path, fixture_set='twenty')
            fixture['companies'][0]['closes'].append('100')
            fixture['companies'][1]['symbol'] = fixture['companies'][0]['symbol']
            path.write_text(json.dumps(fixture))
            with self.assertRaises(ValueError):
                DemoService(directory, fixture_path=path, fixture_set='twenty')

    def test_critic_limit_cannot_be_unbounded(self):
        budget = WorkflowBudget(20, 45, 34560, 80, 1, 1, 0, 64000)
        for limit in (64001, 0, True):
            with self.assertRaises(ValueError):
                replace(budget, max_critic_prompt_characters=limit).validate()

    def test_decimal_weights_exactly_reconcile_without_relaxing_bounds(self):
        for count in (7, 20):
            symbols = tuple('A' + str(i) for i in range(count))
            settings = policy(symbols, max_cash_weight=Decimal('.1'), max_asset_weight=Decimal('.5'))
            result = solve_minimum_variance(settings, np.eye(count))
            self.assertEqual(result.status, 'success')
            self.assertEqual(sum(result.weights.values()) + result.cash_weight, Decimal(1))
            self.assertEqual(result.cash_weight, Decimal('.1'))
            self.assertTrue(all(settings.min_asset_weight <= w <= settings.max_asset_weight for w in result.weights.values()))


if __name__ == '__main__':
    unittest.main()
