"""Deterministic, provider-neutral evidence index with filtered TF-IDF search."""
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re


class EvidenceIndexError(ValueError):
    pass


def _tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _aware(value, field):
    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceIndexError(f"{field} requires a timezone")
    return value


@dataclass(frozen=True)
class EvidenceDocument:
    source_id: str
    symbol: str
    source_type: str
    published_at: datetime
    retrieved_at: datetime
    url: str
    source_sha256: str
    text: str

    def validate(self):
        if not self.source_id or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", self.symbol):
            raise EvidenceIndexError("Invalid evidence identity")
        if self.source_type not in ("sec_filing", "investor_release", "fixture"):
            raise EvidenceIndexError("Unsupported evidence source type")
        _aware(self.published_at, "published_at")
        _aware(self.retrieved_at, "retrieved_at")
        if self.published_at > self.retrieved_at:
            raise EvidenceIndexError("Evidence cannot be retrieved before publication")
        if not self.url.startswith("https://") and self.source_type != "fixture":
            raise EvidenceIndexError("Live evidence requires an HTTPS URL")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise EvidenceIndexError("Invalid source version hash")
        if len(self.text.strip()) < 50:
            raise EvidenceIndexError("Evidence text is too short")
        return self


@dataclass(frozen=True)
class EvidenceChunk:
    chunk_id: str
    source_id: str
    source_sha256: str
    symbol: str
    source_type: str
    published_at: str
    ordinal: int
    text: str


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    source_id: str
    source_sha256: str
    symbol: str
    published_at: str
    score: float
    text: str


def chunk_document(document, chunk_words=180, overlap_words=30):
    document.validate()
    if chunk_words < 20 or overlap_words < 0 or overlap_words >= chunk_words:
        raise EvidenceIndexError("Invalid chunking settings")
    words = document.text.split()
    chunks = []
    step = chunk_words - overlap_words
    for ordinal, start in enumerate(range(0, len(words), step)):
        text = " ".join(words[start:start + chunk_words]).strip()
        if not text:
            continue
        identity = f"{document.source_id}\n{document.source_sha256}\n{ordinal}\n{text}".encode()
        chunks.append(EvidenceChunk(
            hashlib.sha256(identity).hexdigest(), document.source_id, document.source_sha256,
            document.symbol, document.source_type, document.published_at.isoformat(), ordinal, text,
        ))
        if start + chunk_words >= len(words):
            break
    return tuple(chunks)


class LocalEvidenceIndex:
    def __init__(self, chunks, documents, chunk_words=180, overlap_words=30):
        self.chunks = tuple(chunks)
        self.documents = tuple(documents)
        self.chunk_words = chunk_words
        self.overlap_words = overlap_words

    @classmethod
    def build(cls, documents, chunk_words=180, overlap_words=30):
        documents = tuple(document.validate() for document in documents)
        ids = [document.source_id for document in documents]
        if not documents or len(ids) != len(set(ids)):
            raise EvidenceIndexError("Evidence source IDs must be nonempty and unique")
        chunks = tuple(chunk for document in documents for chunk in chunk_document(document, chunk_words, overlap_words))
        return cls(chunks, documents, chunk_words, overlap_words)

    def search(self, query, *, symbols=(), published_after=None, published_before=None, top_k=5):
        query_tokens = _tokens(query)
        if not query_tokens:
            raise EvidenceIndexError("Search query has no searchable terms")
        if top_k < 1 or top_k > 20:
            raise EvidenceIndexError("top_k must be between 1 and 20")
        if published_after:
            _aware(published_after, "published_after")
        if published_before:
            _aware(published_before, "published_before")
        allowed = set(symbols)
        candidates = []
        for chunk in self.chunks:
            published = datetime.fromisoformat(chunk.published_at)
            if allowed and chunk.symbol not in allowed:
                continue
            if published_after and published < published_after:
                continue
            if published_before and published > published_before:
                continue
            candidates.append(chunk)
        if not candidates:
            return ()
        counts = [Counter(_tokens(chunk.text)) for chunk in candidates]
        query_counts = Counter(query_tokens)
        terms = set(query_counts)
        document_frequency = {term: sum(term in count for count in counts) for term in terms}
        idf = {term: math.log((1 + len(candidates)) / (1 + frequency)) + 1 for term, frequency in document_frequency.items()}
        query_norm = math.sqrt(sum((count * idf[term]) ** 2 for term, count in query_counts.items()))
        hits = []
        for chunk, count in zip(candidates, counts):
            numerator = sum(query_counts[term] * count[term] * idf[term] ** 2 for term in terms)
            chunk_norm = math.sqrt(sum((count[term] * idf[term]) ** 2 for term in terms))
            score = numerator / (query_norm * chunk_norm) if numerator and chunk_norm else 0.0
            if score:
                hits.append(SearchHit(chunk.chunk_id, chunk.source_id, chunk.source_sha256, chunk.symbol,
                                      chunk.published_at, round(score, 12), chunk.text))
        return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.chunk_id))[:top_k])

    def save(self, path):
        payload = {
            "schema_version": 1,
            "retriever": "tfidf_cosine_v1",
            "chunk_words": self.chunk_words,
            "overlap_words": self.overlap_words,
            "documents": [{**asdict(document), "published_at": document.published_at.isoformat(),
                           "retrieved_at": document.retrieved_at.isoformat(), "text": None} for document in self.documents],
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or payload.get("retriever") != "tfidf_cosine_v1":
            raise EvidenceIndexError("Unsupported evidence-index format")
        documents = tuple(EvidenceDocument(
            row["source_id"], row["symbol"], row["source_type"], datetime.fromisoformat(row["published_at"]),
            datetime.fromisoformat(row["retrieved_at"]), row["url"], row["source_sha256"], "indexed text stored in chunks",
        ) for row in payload["documents"])
        chunks = tuple(EvidenceChunk(**row) for row in payload["chunks"])
        source_versions = {document.source_id: document.source_sha256 for document in documents}
        if any(source_versions.get(chunk.source_id) != chunk.source_sha256 for chunk in chunks):
            raise EvidenceIndexError("Chunk source version does not match manifest")
        return cls(chunks, documents, payload["chunk_words"], payload["overlap_words"])
