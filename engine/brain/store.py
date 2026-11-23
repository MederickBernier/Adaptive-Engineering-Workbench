"""Transactional SQLite persistence for published project knowledge."""

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from engine.brain.model import (
    Assertion,
    Depth,
    Evidence,
    KnowledgeKind,
    Revision,
    Snapshot,
    Verification,
    validate_path,
)

_SCHEMA_VERSION = 1
_SCHEMA = (
    "CREATE TABLE project (id INTEGER PRIMARY KEY CHECK (id = 1), repository TEXT NOT NULL)",
    (
        "CREATE TABLE snapshots (id TEXT PRIMARY KEY, revision TEXT NOT NULL, "
        "regions TEXT NOT NULL, observed_at TEXT NOT NULL)"
    ),
    "CREATE TABLE assertions (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL)",
    (
        "CREATE TABLE membership (snapshot_id TEXT NOT NULL REFERENCES snapshots(id), "
        "assertion_id TEXT NOT NULL REFERENCES assertions(id), "
        "PRIMARY KEY (snapshot_id, assertion_id))"
    ),
)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _identity(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


def _decode_assertion(payload: str) -> Assertion:
    data = json.loads(payload)
    data["revision"] = Revision(**data["revision"])
    data["evidence"] = tuple(Evidence(**item) for item in data["evidence"])
    data["kind"] = KnowledgeKind(data["kind"])
    data["depth"] = Depth(data["depth"])
    data["verification"] = Verification(data["verification"])
    return Assertion(**data)


class ProjectBrain:
    """A caller-selected SQLite database permanently bound to one repository."""

    def __init__(self, path: Path, repository: str) -> None:
        if not repository.strip():
            raise ValueError("Repository identity is required")
        self.path = path.resolve()
        self.repository = repository
        with self._write() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                for statement in _SCHEMA:
                    db.execute(statement)
                db.execute("INSERT INTO project VALUES (1, ?)", (repository,))
                db.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif version != _SCHEMA_VERSION:
                raise ValueError(f"Unsupported Project Brain schema version: {version}")
            self._check_identity(db)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            yield db

    def _check_identity(self, db: sqlite3.Connection) -> None:
        row = db.execute("SELECT repository FROM project WHERE id = 1").fetchone()
        if row != (self.repository,):
            raise ValueError("Project Brain is bound to a different repository")

    def publish(
        self,
        revision: Revision,
        regions: Iterable[str],
        assertions: Iterable[Assertion],
    ) -> Snapshot:
        """Publish a coherent snapshot and its explicit membership atomically."""
        if revision.repository != self.repository:
            raise ValueError("Snapshot repository does not match the Project Brain")
        coverage = tuple(sorted(set(regions)))
        for region in coverage:
            if region != ".":
                validate_path(region)

        records: dict[str, tuple[str, str]] = {}
        for assertion in assertions:
            if assertion.revision != revision:
                raise ValueError("Assertion revision does not match the snapshot")
            if assertion.region not in coverage:
                raise ValueError("Assertion region is outside snapshot coverage")
            payload = _json(asdict(assertion))
            records[_identity(payload)] = (assertion.kind.value, payload)

        revision_payload = _json(asdict(revision))
        coverage_payload = _json(coverage)
        members = sorted(records)
        snapshot_id = _identity(_json((revision_payload, coverage_payload, members)))
        with self._write() as db:
            self._check_identity(db)
            exists = db.execute(
                "SELECT 1 FROM snapshots WHERE id = ?", (snapshot_id,)
            ).fetchone()
            if exists is None:
                db.execute(
                    "INSERT INTO snapshots VALUES (?, ?, ?, ?)",
                    (
                        snapshot_id,
                        revision_payload,
                        coverage_payload,
                        datetime.now(UTC).isoformat(),
                    ),
                )
                db.executemany(
                    "INSERT INTO assertions VALUES (?, ?, ?) ON CONFLICT(id) DO NOTHING",
                    ((key, *records[key]) for key in members),
                )
                db.executemany(
                    "INSERT INTO membership VALUES (?, ?)",
                    ((snapshot_id, key) for key in members),
                )
        return self.load(snapshot_id)

    def load(self, snapshot_id: str) -> Snapshot:
        """Reconstruct a published snapshot without consulting the worktree."""
        with closing(self._connect()) as db:
            self._check_identity(db)
            row = db.execute(
                "SELECT revision, regions, observed_at FROM snapshots WHERE id = ?",
                (snapshot_id,),
            ).fetchone()
            if row is None:
                raise KeyError(snapshot_id)
            revision, regions, observed_at = row
            assertions = db.execute(
                "SELECT a.payload FROM membership AS m JOIN assertions AS a ON a.id = m.assertion_id "
                "WHERE m.snapshot_id = ? ORDER BY a.id",
                (snapshot_id,),
            )
            return Snapshot(
                snapshot_id,
                Revision(**json.loads(revision)),
                tuple(json.loads(regions)),
                tuple(_decode_assertion(payload) for (payload,) in assertions),
                observed_at,
            )
