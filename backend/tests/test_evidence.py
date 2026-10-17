"""Offline document-evidence access-proof tests."""
from io import BytesIO
import unittest
from unittest.mock import Mock
from backend.app.adapters.data.evidence import EvidenceClient, EvidenceError, allowed_release_url, evidence_record, sec_filing_url


class EvidenceTests(unittest.TestCase):
    def test_sec_url_validation(self):
        self.assertEqual(sec_filing_url("0000789019", "0000950170-25-010491", "msft-20241231.htm"), "https://www.sec.gov/Archives/edgar/data/789019/000095017025010491/msft-20241231.htm")
        for document in ("../../x", "x?y", ""):
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    sec_filing_url("0000789019", "0000950170-25-010491", document)

    def test_release_allowlist(self):
        valid = "https://www.microsoft.com/en-us/investor/earnings/fy-2025-q2/press-release-webcast"
        self.assertEqual(allowed_release_url(valid), valid)
        for url in ("http://www.microsoft.com/en-us/investor/x", "https://example.com/en-us/investor/x", valid + "?x=1"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    allowed_release_url(url)

    def test_fetch_provenance_and_budget(self):
        body = b"<html><title>Test</title><body>" + b"x" * 300 + b"</body></html>"
        opener = Mock(side_effect=lambda *args, **kwargs: BytesIO(body))
        client = EvidenceClient("Test test@example.invalid", opener)
        html, metadata = client.fetch_html("https://example.test", "sec_filing")
        self.assertEqual(metadata["source_type"], "sec_filing")
        self.assertNotIn("example.invalid", str(metadata))
        record = evidence_record(html, metadata, "TEST", "2025-01-01")
        self.assertEqual(record["content_stored"], False)
        client.fetch_html("https://example.test", "investor_release")
        with self.assertRaises(EvidenceError) as caught:
            client.fetch_html("https://example.test", "sec_filing")
        self.assertEqual(caught.exception.status, "awaiting_quota")

    def test_expected_markers_and_short_content(self):
        metadata = {"source_type": "release", "url": "https://x", "sha256": "a"}
        with self.assertRaises(ValueError):
            evidence_record("<p>short</p>", metadata, "TEST", "2025", ("date",))
        with self.assertRaises(ValueError):
            evidence_record("<p>" + "x" * 300 + "</p>", metadata, "TEST", "2025", ("missing",))

    def test_missing_identity(self):
        with self.assertRaises(EvidenceError) as caught:
            EvidenceClient("")
        self.assertEqual(caught.exception.status, "missing_configuration")


if __name__ == "__main__":
    unittest.main()


