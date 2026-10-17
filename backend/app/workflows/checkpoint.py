"""Atomic local JSON checkpoints with allowlisted dataclass decoding."""
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from decimal import Decimal
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re

from backend.app.application.selection import CandidateDecision, SelectionResult
from backend.app.domain.optimizer import PortfolioResult
from backend.app.domain.statistics import PriceStatistics
from backend.app.research.fundamental import FundamentalReport, ResearchFinding
from backend.app.research.news import NewsReport, NewsFinding
from backend.app.research.quantitative import QuantitativeReport
from backend.app.retrieval.index import SearchHit

TYPES = {cls.__name__: cls for cls in (CandidateDecision, SelectionResult, PortfolioResult, PriceStatistics,
         FundamentalReport, ResearchFinding, NewsReport, NewsFinding, QuantitativeReport, SearchHit)}


class CheckpointError(ValueError):
    pass


def encode(value):
    if is_dataclass(value):
        return {"$type": type(value).__name__, "fields": {f.name: encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, tuple):
        return {"$tuple": [encode(v) for v in value]}
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    # Preserve dates in policy snapshots across a checkpoint round trip.
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    return value


def decode(value):
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, dict):
        if "$type" in value:
            cls = TYPES.get(value["$type"])
            if cls is None or set(value) != {"$type", "fields"}:
                raise CheckpointError("Unknown checkpoint type")
            return cls(**{k: decode(v) for k, v in value["fields"].items()})
        if set(value) == {"$datetime"}:
            return datetime.fromisoformat(value["$datetime"] )
        if set(value) == {"$date"}:
            return date.fromisoformat(value["$date"] )
        if set(value) == {"$decimal"}:
            return Decimal(value["$decimal"])
        if set(value) == {"$tuple"}:
            return tuple(decode(v) for v in value["$tuple"])
        return {k: decode(v) for k, v in value.items()}
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class JsonCheckpointStore:
    """One writer per run; stale crash locks require explicit operator removal."""
    def __init__(self, directory):
        self.directory = Path(directory)

    def path(self, run_id):
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", run_id):
            raise CheckpointError("Invalid run ID")
        return self.directory / (run_id + ".json")

    @contextmanager
    def locked(self, run_id):
        path = self.path(run_id).with_suffix(".lock")
        self.directory.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise CheckpointError("Run is locked; verify no active writer before removing a stale lock") from None
        try:
            os.close(fd)
            yield
        finally:
            path.unlink()

    def save(self, run_id, state):
        payload = encode(state)
        checksum = hashlib.sha256(canonical(payload).encode()).hexdigest()
        text = canonical({"schema_version": 1, "sha256": checksum, "payload": payload})
        path = self.path(run_id)
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def load(self, run_id):
        path = self.path(run_id)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if (envelope["schema_version"] != 1 or
                    hashlib.sha256(canonical(envelope["payload"]).encode()).hexdigest() != envelope["sha256"]):
                raise CheckpointError("Checkpoint version/checksum mismatch")
            return decode(envelope["payload"])
        except (ValueError, TypeError, KeyError) as exc:
            raise CheckpointError("Invalid checkpoint; no calls made") from exc

