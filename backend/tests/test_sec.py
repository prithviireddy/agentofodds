"""Offline SEC contract/transport checks. No real identities or network calls."""
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
import json
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import Mock

from backend.app.adapters.data.sec import (
    SecClient, SecError, TICKERS, eligible_assets, eligible_filings, resolve_symbols,
)
from backend.app.sec_probe import run
from backend.app.config.universe import Company, Universe

CIK = '0000000001'
ACC = '0000000001-25-000001'
CUTOFF = datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc)


def facts():
    return {'cik': 1, 'facts': {'us-gaap': {'Assets': {'units': {'USD': [
        {'end': '2024-12-31', 'filed': '2025-01-30', 'form': '10-Q', 'val': 100,
         'accn': ACC}
    ]}}}}}


def filings():
    return {'cik': 1, 'filings': {'recent': {
        'accessionNumber': [ACC], 'filingDate': ['2025-01-30'],
        'form': ['10-Q'], 'primaryDocument': ['synthetic.htm']}}}


class SecTests(unittest.TestCase):
    def client(self, opener=None):
        return SecClient('OfflineTest test@example.invalid', opener=opener or Mock(),
                         sleep=Mock(), clock=lambda: 0.0)

    def test_missing_identity_makes_no_request(self):
        opener = Mock()
        with self.assertRaises(SecError) as caught:
            SecClient('', opener=opener)
        self.assertEqual(caught.exception.status, 'missing_configuration')
        opener.assert_not_called()

    def test_header_injection_rejected(self):
        with self.assertRaises(SecError):
            SecClient('Test\r\nInjected: x test@example.invalid')

    def test_allowlist_blocks_external_destinations(self):
        client = self.client()
        for url in ('https://example.com', 'https://data.sec.gov.evil.org/submissions/CIK0000000001.json',
                    'http://www.sec.gov/files/company_tickers.json'):
            with self.assertRaises(SecError):
                client.fetch(url)
        client.opener.assert_not_called()

    def test_transport_provenance_and_decimal_precision(self):
        opener = Mock(return_value=BytesIO(b'{"value": 1.1234567890123456789}'))
        client = self.client(opener)
        result, source = client.fetch(TICKERS)
        self.assertEqual(result['value'], Decimal('1.1234567890123456789'))
        self.assertEqual(source['url'], TICKERS)
        self.assertEqual(len(source['sha256']), 64)
        self.assertEqual(opener.call_args.kwargs['timeout'], 20)
        self.assertNotIn('test@example.invalid', json.dumps(source))

    def test_rate_limit_and_call_budget(self):
        opener = Mock(side_effect=lambda *a, **kw: BytesIO(b'{}'))
        client = self.client(opener)
        for _ in range(12):
            client.fetch(TICKERS)
        with self.assertRaises(SecError) as caught:
            client.fetch(TICKERS)
        self.assertEqual(caught.exception.status, 'awaiting_quota')
        self.assertEqual(opener.call_count, 12)
        self.assertEqual(client.sleep.call_count, 11)
        client.sleep.assert_called_with(1.0)

    def test_http_errors_do_not_retry(self):
        for code, expected in ((429, 'awaiting_quota'), (403, 'provider_error'), (503, 'provider_error')):
            with self.subTest(code=code):
                opener = Mock(side_effect=HTTPError(TICKERS, code, '', {}, None))
                with self.assertRaises(SecError) as caught:
                    self.client(opener).fetch(TICKERS)
                self.assertEqual(caught.exception.status, expected)
                self.assertEqual(opener.call_count, 1)

    def test_transport_failure(self):
        with self.assertRaises(SecError) as caught:
            self.client(Mock(side_effect=URLError('private details'))).fetch(TICKERS)
        self.assertEqual(caught.exception.status, 'provider_error')
        self.assertNotIn('private details', str(caught.exception))

    def test_invalid_json(self):
        for raw in (b'not json', b'[]'):
            with self.assertRaises(SecError) as caught:
                self.client(Mock(return_value=BytesIO(raw))).fetch(TICKERS)
            self.assertEqual(caught.exception.status, 'failed_validation')

    def test_identity_resolution_and_missing_symbols(self):
        rows = {'0': {'ticker': 'TEST', 'cik_str': 1, 'title': 'Synthetic Company'}}
        self.assertEqual(resolve_symbols(rows, ('TEST',))['TEST']['cik'], CIK)
        with self.assertRaises(ValueError):
            resolve_symbols(rows, ('MISSING',))
        rows['1'] = rows['0']
        with self.assertRaises(ValueError):
            resolve_symbols(rows, ('TEST',))

    def test_filed_date_cutoff_excludes_later_restatement(self):
        payload = facts()
        rows = payload['facts']['us-gaap']['Assets']['units']['USD']
        rows.append({**rows[0], 'filed': '2025-02-01', 'val': 999, 'accn': '0000000001-25-000002'})
        result = eligible_assets(payload, CIK, CUTOFF)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], '100')
        self.assertEqual(result[0]['unit'], 'USD')
        self.assertEqual(result[0]['available_at'], '2025-01-31T05:00:00+00:00')

    def test_same_day_is_conservatively_excluded(self):
        cutoff = datetime(2025, 1, 30, 23, 59, tzinfo=timezone.utc)
        self.assertEqual(eligible_assets(facts(), CIK, cutoff), [])
        self.assertEqual(eligible_filings(filings(), CIK, cutoff), [])

    def test_wrong_company_and_invalid_values(self):
        with self.assertRaises(ValueError):
            eligible_assets(facts(), '2', CUTOFF)
        with self.assertRaises(ValueError):
            eligible_filings(filings(), '2', CUTOFF)
        payload = facts()
        payload['facts']['us-gaap']['Assets']['units']['USD'][0]['val'] = float('nan')
        with self.assertRaises(ValueError):
            eligible_assets(payload, CIK, CUTOFF)

    def test_no_unit_substitution(self):
        payload = facts()
        units = payload['facts']['us-gaap']['Assets']['units']
        units['EUR'] = units.pop('USD')
        self.assertEqual(eligible_assets(payload, CIK, CUTOFF), [])

    def test_filing_arrays_and_paths_validated(self):
        payload = filings()
        self.assertIn('/1/000000000125000001/synthetic.htm', eligible_filings(payload, CIK, CUTOFF)[0]['url'])
        payload['filings']['recent']['primaryDocument'] = ['../../outside']
        with self.assertRaises(ValueError):
            eligible_filings(payload, CIK, CUTOFF)
        payload['filings']['recent']['primaryDocument'] = []
        with self.assertRaises(ValueError):
            eligible_filings(payload, CIK, CUTOFF)

    def test_probe_with_fake_transport(self):
        universe = Universe('test', CUTOFF, 'synthetic', (Company('TEST', 'Synthetic', 'Test', 'Test', CIK),))
        client = Mock()
        client.fetch.side_effect = [({'0': {'ticker': 'TEST', 'cik_str': 1, 'title': 'Synthetic'}}, {}),
                                    (facts(), {}), (filings(), {})]
        result = run(universe, client)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(client.fetch.call_count, 3)
        self.assertEqual(result['companies'][0]['asset_sample']['value'], '100')


if __name__ == '__main__':
    unittest.main()

class DotenvTests(unittest.TestCase):
    def test_dotenv_does_not_override_environment(self):
        from backend.app.sec_probe import load_dotenv
        from pathlib import Path
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / '.env'
            path.write_text('SEC_USER_AGENT=File Name file@example.invalid\n')
            previous = os.environ.get('SEC_USER_AGENT')
            os.environ['SEC_USER_AGENT'] = 'Shell Name shell@example.invalid'
            try:
                load_dotenv(path)
                self.assertEqual(os.environ['SEC_USER_AGENT'], 'Shell Name shell@example.invalid')
            finally:
                if previous is None:
                    os.environ.pop('SEC_USER_AGENT', None)
                else:
                    os.environ['SEC_USER_AGENT'] = previous

    def test_dotenv_bad_line_rejected(self):
        from backend.app.sec_probe import load_dotenv
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / '.env'
            path.write_text('NO_EQUALS\n')
            with self.assertRaisesRegex(ValueError, 'line 1'):
                load_dotenv(path)

