"""Controlled fixture comparisons, held-out input isolation and archive replay."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.app.adapters.comparison_fixture import CombinedFixtureModel
from backend.app.application.demo import DemoService, FixtureModel
from backend.app.evaluation.comparison import (run_comparison, replay_comparison, evaluate_decisions,
    prepare_decisions, decision_identity, validate_plan, VARIANTS)
from backend.app.research.combined import run_combined_research
from backend.app.retrieval.index import LocalEvidenceIndex


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_comparison()

    def test_all_variants_same_policy_costs_and_equal_output_caps(self):
        for run in self.result['runs']:
            count = len(run['decisions']['policy']['symbols'])
            variants = run['decisions']['variants']
            for name in VARIANTS:
                self.assertEqual(run['results'][name]['status'], 'success')
                book = run['results'][name]['opening_book']
                self.assertEqual(book['fee_bps'], '10')
                self.assertEqual(book['balances']['capital'], '10000')
                self.assertEqual(book['balances']['fees'], '9')
            self.assertEqual(variants['combined_researcher']['usage']['scripted_calls'], count + 1)
            self.assertEqual(variants['separate_researchers']['usage']['scripted_calls'], 2 * count + 1)
            self.assertEqual(variants['combined_researcher']['usage']['reserved_output_tokens'],
                             variants['separate_researchers']['usage']['reserved_output_tokens'])
            self.assertIsNone(variants['combined_researcher']['usage']['actual_tokens'])
            self.assertIsNone(variants['separate_researchers']['usage']['inference_cost_usd'])
            self.assertEqual(variants['numerical_only']['portfolio']['weights'], variants['combined_researcher']['portfolio']['weights'])
            self.assertEqual(variants['combined_researcher']['portfolio']['weights'], variants['separate_researchers']['portfolio']['weights'])

    def test_archive_replay_requires_no_files_or_model_calls(self):
        with patch.object(FixtureModel, 'generate_json', side_effect=AssertionError('Model called')), \
             patch.object(CombinedFixtureModel, 'generate_json', side_effect=AssertionError('Model called')), \
             patch.object(Path, 'read_bytes', side_effect=AssertionError('Read external source')):
            self.assertEqual(replay_comparison(self.result), self.result)

    def test_archive_corruption_refused(self):
        for kind in ('source', 'decision', 'evaluation', 'plan'):
            result = deepcopy(self.result)
            if kind == 'source':
                result['source_archive']['comparison_holdout.json']['text'] += ' '
            elif kind == 'decision':
                result['runs'][0]['decisions']['variants']['equal_weight']['candidates'].pop()
            elif kind == 'evaluation':
                result['runs'][0]['results']['equal_weight']['evaluations']['holdout']['equity'] = '999'
            else:
                result['plan']['transaction_cost_bps'] = '0'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                replay_comparison(result)

    def test_decisions_never_read_evaluation_files_and_reproduce(self):
        read = Path.read_bytes
        def guarded(path):
            if 'paper_' in path.name or 'holdout' in path.name:
                raise AssertionError('Decision phase read future prices')
            return read(path)
        with patch.object(Path, 'read_bytes', guarded):
            fresh = prepare_decisions('five')
        self.assertEqual(decision_identity(fresh), self.result['runs'][0]['decisions_sha256'])

    def inputs(self):
        archive = self.result['source_archive']
        return [deepcopy(self.result['runs'][0]['decisions']), deepcopy(self.result['plan']),
                *[json.loads(archive[name]['text']) for name in ('paper_fills.json', 'paper_valuations.json', 'comparison_holdout.json')]]

    def test_holdout_changes_outcomes_without_changing_decisions(self):
        args = self.inputs()
        identity = decision_identity(args[0])
        baseline = evaluate_decisions(*args)
        for row in args[-1]['frames'][0]['prices']:
            row['close'] = '200'
        changed = evaluate_decisions(*args)
        self.assertEqual(decision_identity(args[0]), identity)
        self.assertEqual(changed['combined_researcher']['evaluations']['development'], baseline['combined_researcher']['evaluations']['development'])
        self.assertNotEqual(changed['combined_researcher']['evaluations']['holdout'], baseline['combined_researcher']['evaluations']['holdout'])

    def test_invalid_holdout_cannot_produce_comparison_metrics(self):
        for change, status in (('missing', 'missing_prices'), ('future', 'future_prices'),
                               ('action', 'unsupported_corporate_action'), ('stale', 'stale_prices')):
            args = self.inputs()
            frame = args[-1]['frames'][0]
            if change == 'missing':
                frame['prices'] = []
            elif change == 'future':
                frame['prices'][0]['available_at'] = '2025-02-15T00:00:00Z'
            elif change == 'action':
                frame['corporate_actions'] = [{'kind': 'split'}]
            else:
                frame['prices'][0]['session'] = '2025-02-10'
            results = evaluate_decisions(*args)
            for result in results.values():
                self.assertEqual(result['status'], status)
                self.assertEqual(result['evaluations'], {})

    def test_plan_overlap_or_fee_invalid_rejected(self):
        for change in ({'holdout_valuation_at': '2025-02-04T22:00:00Z'}, {'transaction_cost_bps': '-1'},
                       {'transaction_cost_bps': 'NaN'}, {'tuning': 'optimise_holdout'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_plan({**self.result['plan'], **change})

    def test_failed_research_is_not_evaluated(self):
        args = self.inputs()
        args[0]['variants']['combined_researcher']['status'] = 'awaiting_quota'
        result = evaluate_decisions(*args)['combined_researcher']
        self.assertEqual(result, {'status': 'awaiting_quota', 'evaluations': {}})

    def test_report_uses_declared_cost_and_does_not_claim_parity_on_failure(self):
        from backend.app.compare_experiments import markdown
        result = deepcopy(self.result)
        result['plan']['transaction_cost_bps'] = '15'
        result['runs'][0]['results']['combined_researcher'] = {'status': 'failed_validation', 'evaluations': {}}
        report = markdown(result)
        self.assertIn('15 bps', report)
        self.assertNotIn('Research allocations match', report)
        self.assertIn('unavailable', report)


class CombinedTests(unittest.TestCase):
    def setUp(self):
        self.service = DemoService()
        self.inputs = self.service.inputs(self.service.settings()['demo'])
        self.request = self.inputs['requests']['MSFT']

    def run_role(self, model, index=None):
        return run_combined_research(index or self.inputs['index'], self.request, self.inputs['news_start'], model)

    def test_one_call_two_valid_role_contracts(self):
        model = CombinedFixtureModel()
        fundamental, news = self.run_role(model)
        self.assertEqual(len(model.events), 1)
        self.assertEqual(fundamental.status, 'success')
        self.assertEqual(news.status, 'success')
        self.assertEqual(fundamental.model_metadata, news.model_metadata)

    def test_invalid_citation_or_role_keys_rejected(self):
        for corruption in ('citation', 'keys'):
            class Invalid(CombinedFixtureModel):
                def generate_json(self, *args, **kwargs):
                    output, metadata = super().generate_json(*args, **kwargs)
                    if corruption == 'citation':
                        output['news']['findings'][0]['citation_chunk_ids'] = ['not-visible']
                    else:
                        output['unexpected'] = 'value'
                    return output, metadata
            with self.assertRaises(ValueError):
                self.run_role(Invalid())

    def test_empty_or_future_evidence_does_not_call_model(self):
        for index in (LocalEvidenceIndex((), ()), LocalEvidenceIndex.build(tuple(
                replace(d, published_at=d.retrieved_at.replace(year=2030), retrieved_at=d.retrieved_at.replace(year=2030))
                for d in self.inputs['index'].documents))):
            model = CombinedFixtureModel()
            reports = self.run_role(model, index)
            self.assertEqual(model.events, [])
            self.assertEqual([r.status for r in reports], ['insufficient_evidence', 'insufficient_evidence'])


if __name__ == '__main__':
    unittest.main()
