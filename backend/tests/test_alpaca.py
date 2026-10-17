"""Offline Alpaca access-proof tests."""
from decimal import Decimal
from io import BytesIO
import json
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from backend.app.adapters.data.alpaca import AlpacaMarketDataClient, AlpacaError, normalise_daily_bars


class AlpacaTests(unittest.TestCase):
    def client(self, opener=None):
        return AlpacaMarketDataClient("test-key", "test-secret", opener or Mock())

    def test_missing_credentials_never_request(self):
        with self.assertRaises(AlpacaError) as caught:
            AlpacaMarketDataClient("", "secret")
        self.assertEqual(caught.exception.status, "missing_configuration")

    def test_request_shape_and_secret_not_in_provenance(self):
        opener = Mock(return_value=BytesIO(b'{"bars":{"TEST":[{"t":"2025-01-30T05:00:00Z","c":123.45}]}}'))
        payload, source = self.client(opener).daily_bars(("TEST",), "2025-01-30T00:00:00Z", "2025-02-01T00:00:00Z")
        request = opener.call_args.args[0]
        self.assertIn("timeframe=1Day", request.full_url)
        self.assertIn("feed=iex", request.full_url)
        self.assertEqual(request.headers["Apca-api-key-id"], "test-key")
        self.assertNotIn("test-secret", json.dumps(source))
        bars, missing = normalise_daily_bars(payload, ("TEST",))
        self.assertEqual(bars[0]["close"], "123.45")
        self.assertEqual(missing, [])

    def test_missing_symbols_and_bad_bars_are_explicit(self):
        self.assertEqual(normalise_daily_bars({"bars": {}}, ("TEST",))[1], ["TEST"])
        with self.assertRaises(ValueError):
            normalise_daily_bars({"bars": {"TEST": [{"t": "bad", "c": "NaN"}]}}, ("TEST",))

    def test_one_request_budget_and_required_conventions(self):
        client = self.client(Mock(return_value=BytesIO(b'{"bars":{}}')))
        with self.assertRaises(ValueError):
            client.daily_bars(("TEST",), "2025-01-30T00:00:00Z", "2025-02-01T00:00:00Z", feed="sip")
        client.daily_bars(("TEST",), "2025-01-30T00:00:00Z", "2025-02-01T00:00:00Z")
        with self.assertRaises(AlpacaError) as caught:
            client.daily_bars(("TEST",), "2025-01-30T00:00:00Z", "2025-02-01T00:00:00Z")
        self.assertEqual(caught.exception.status, "awaiting_quota")

    def test_http_error_no_retry(self):
        opener = Mock(side_effect=HTTPError("url", 429, "", {}, None))
        with self.assertRaises(AlpacaError) as caught:
            self.client(opener).daily_bars(("TEST",), "2025-01-30T00:00:00Z", "2025-02-01T00:00:00Z")
        self.assertEqual(caught.exception.status, "awaiting_quota")
        self.assertEqual(opener.call_count, 1)


if __name__ == "__main__":
    unittest.main()
