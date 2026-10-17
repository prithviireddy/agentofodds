"""M2.1 evidence versioning, chunking, persistence and filter tests."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from backend.app.retrieval.index import EvidenceDocument, EvidenceIndexError, LocalEvidenceIndex, chunk_document


def moment(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def document(source_id, symbol, published, text, version="a" * 64):
    return EvidenceDocument(source_id, symbol, "fixture", moment(published), moment("2025-02-10T00:00:00"),
                            "fixture://local", version, text)


MSFT = document("fixture:msft:v1", "MSFT", "2025-01-29T00:00:00",
                "Microsoft cloud revenue increased while operating income also increased. " * 12)
JPM = document("fixture:jpm:v1", "JPM", "2025-02-05T00:00:00",
               "JPMorgan reported banking revenue and credit costs for the quarter. " * 12, "b" * 64)


class EvidenceIndexTests(unittest.TestCase):
    def test_chunks_are_deterministic_and_version_bound(self):
        first = chunk_document(MSFT, 20, 5)
        second = chunk_document(MSFT, 20, 5)
        changed = chunk_document(document("fixture:msft:v1", "MSFT", "2025-01-29T00:00:00", MSFT.text, "c" * 64), 20, 5)
        self.assertEqual(first, second)
        self.assertNotEqual(first[0].chunk_id, changed[0].chunk_id)

    def test_search_ranks_matching_evidence(self):
        index = LocalEvidenceIndex.build((MSFT, JPM), 30, 5)
        hits = index.search("cloud operating income", top_k=2)
        self.assertTrue(hits)
        self.assertEqual(hits[0].symbol, "MSFT")
        self.assertEqual(hits[0].source_sha256, "a" * 64)

    def test_company_and_date_filters_apply_before_search(self):
        index = LocalEvidenceIndex.build((MSFT, JPM), 30, 5)
        self.assertEqual(index.search("revenue", symbols=("JPM",))[0].symbol, "JPM")
        cutoff = moment("2025-01-31T23:59:59")
        self.assertTrue(all(hit.symbol == "MSFT" for hit in index.search("revenue", published_before=cutoff)))
        self.assertEqual(index.search("revenue", symbols=("JPM",), published_before=cutoff), ())

    def test_save_load_preserves_results_and_omits_full_document_text(self):
        index = LocalEvidenceIndex.build((MSFT, JPM), 30, 5)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            index.save(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsNone(payload["documents"][0]["text"])
            loaded = LocalEvidenceIndex.load(path)
            self.assertEqual(index.search("credit costs"), loaded.search("credit costs"))

    def test_load_rejects_chunk_source_version_mismatch(self):
        index = LocalEvidenceIndex.build((MSFT,), 30, 5)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            index.save(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["chunks"][0]["source_sha256"] = "f" * 64
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(EvidenceIndexError):
                LocalEvidenceIndex.load(path)

    def test_invalid_documents_and_unbounded_queries_fail(self):
        with self.assertRaises(EvidenceIndexError):
            LocalEvidenceIndex.build((document("", "MSFT", "2025-01-29T00:00:00", MSFT.text),))
        index = LocalEvidenceIndex.build((MSFT,))
        for query, top_k in (("", 5), ("revenue", 21)):
            with self.subTest(query=query, top_k=top_k):
                with self.assertRaises(EvidenceIndexError):
                    index.search(query, top_k=top_k)


if __name__ == "__main__":
    unittest.main()
