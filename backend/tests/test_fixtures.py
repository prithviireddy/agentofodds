import copy
from datetime import date, datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from backend.app.adapters.data.fixture import load_prices
from backend.app.config.universe import load_universe
from backend.app.contracts.market_data import timestamp

ROOT = Path(__file__).resolve().parents[2]


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.universe = load_universe(ROOT / 'config/universe.toml')
        self.raw = json.loads((ROOT / 'fixtures/prices.json').read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'prices.json'

    def query(self, raw=None, symbols=None, cutoff=None):
        self.path.write_text(json.dumps(self.raw if raw is None else raw))
        return load_prices(self.path, self.universe.symbols if symbols is None else symbols,
                           self.universe.as_of if cutoff is None else cutoff,
                           date(2025, 1, 30), date(2025, 1, 31))

    def test_complete_fixture_and_provenance(self):
        result = self.query()
        self.assertEqual(result.status, 'success')
        self.assertEqual(len(result.bars), 10)
        self.assertEqual(result.metadata['kind'], 'synthetic')
        self.assertEqual(len(result.metadata['sha256']), 64)
        self.assertEqual(str(result.bars[-1].close), '102.00')

    def test_cutoff_excludes_late_publication_not_just_session(self):
        raw = copy.deepcopy(self.raw)
        raw['bars'][0]['available_at'] = '2025-02-01T00:00:00Z'
        result = self.query(raw)
        self.assertEqual(len(result.bars), 9)
        self.assertEqual(result.excluded_after_cutoff, 1)
        self.assertFalse(any(b.source_id == raw['bars'][0]['source_id'] for b in result.bars))

    def test_cutoff_boundary_inclusive(self):
        result = self.query(cutoff=timestamp('2025-01-30T22:00:00Z'))
        self.assertEqual(len(result.bars), 5)
        self.assertEqual(result.excluded_after_cutoff, 5)

    def test_empty_history_explicit(self):
        result = self.query(cutoff=timestamp('2025-01-29T22:00:00Z'))
        self.assertEqual(result.status, 'partial_data')
        self.assertEqual(result.missing_symbols, self.universe.symbols)
        self.assertEqual(result.bars, ())

    def test_missing_symbol_and_arbitrary_universe_size(self):
        result = self.query(symbols=('MSFT', 'UNKNOWN'))
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(result.missing_symbols, ('UNKNOWN',))
        self.assertEqual(result.status, 'partial_data')

    def test_invalid_values(self):
        for close in ('NaN', 'Infinity', '-1', '0', 'oops', 10.5, True):
            with self.subTest(close=close):
                raw = copy.deepcopy(self.raw)
                raw['bars'][0]['close'] = close
                with self.assertRaises(ValueError):
                    self.query(raw)

    def test_duplicate_price_rejected(self):
        self.raw['bars'].append(self.raw['bars'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.query()

    def test_invalid_units_and_unlabelled_fixture_rejected(self):
        for key, value in [('currency', 'EUR'), ('kind', 'live'), ('adjustment', 'split')]:
            with self.subTest(key=key):
                raw = copy.deepcopy(self.raw)
                raw[key] = value
                with self.assertRaises(ValueError):
                    self.query(raw)

    def test_naive_dates_rejected(self):
        with self.assertRaises(ValueError):
            self.query(cutoff=datetime(2025, 1, 31))
        self.raw['bars'][0]['available_at'] = '2025-01-30T22:00:00'
        with self.assertRaises(ValueError):
            self.query()

    def test_universe_size_and_duplicates(self):
        original = (ROOT / 'config/universe.toml').read_text()
        sections = original.split('[[companies]]')
        config = Path(self.temp.name) / 'universe.toml'
        config.write_text(sections[0] + '[[companies]]' + sections[1])
        self.assertEqual(load_universe(config).symbols, ('MSFT',))
        config.write_text(original + '[[companies]]' + sections[1])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            load_universe(config)

    def test_cli_structured_failure(self):
        result = subprocess.run([sys.executable, '-m', 'backend.app', '--as-of', 'invalid'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'failed_validation')

    def test_cli_partial_data_exit(self):
        result = subprocess.run([sys.executable, '-m', 'backend.app', '--as-of',
                                 '2025-01-01T00:00:00Z'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'partial_data')


if __name__ == '__main__':
    unittest.main()
