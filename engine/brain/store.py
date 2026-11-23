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
    validate_commit,
    validate_path,
)

_SCHEMA_VERSION = 2
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
_PLAN_SCHEMA = (
    "CREATE TABLE plan_revisions (plan_id TEXT NOT NULL, revision INTEGER NOT NULL, "
    "recorded_at TEXT NOT NULL, material TEXT NOT NULL, payload TEXT NOT NULL, "
    "changes TEXT NOT NULL, PRIMARY KEY (plan_id, revision))"
)


class SnapshotIntegrityError(ValueError):
    """A stored snapshot or assertion no longer matches its published identity."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _identity(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


def assertion_id(assertion: Assertion) -> str:
    """Return the stable identifier used for snapshot membership."""
    return _identity(_json(asdict(assertion)))


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
            elif version not in (1, _SCHEMA_VERSION):
                raise ValueError(f"Unsupported Project Brain schema version: {version}")
            self._check_identity(db)
            if version < 2:
                db.execute(_PLAN_SCHEMA)
                db.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")

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
            db.execute("BEGIN")
            self._check_identity(db)
            row = db.execute(
                "SELECT revision, regions, observed_at FROM snapshots WHERE id = ?",
                (snapshot_id,),
            ).fetchone()
            if row is None:
                raise KeyError(snapshot_id)
            revision, regions, observed_at = row
            members = db.execute(
                "SELECT m.assertion_id, a.payload, a.kind FROM membership AS m "
                "LEFT JOIN assertions AS a ON a.id = m.assertion_id "
                "WHERE m.snapshot_id = ? ORDER BY m.assertion_id",
                (snapshot_id,),
            ).fetchall()
            if (
                _identity(_json((revision, regions, [key for key, _, _ in members])))
                != snapshot_id
            ):
                raise SnapshotIntegrityError(
                    "Snapshot metadata or membership does not match its ID"
                )
            try:
                bound_revision = Revision(**json.loads(revision))
                coverage = tuple(json.loads(regions))
                assertions = []
                for key, payload, kind in members:
                    if payload is None or _identity(payload) != key:
                        raise SnapshotIntegrityError(
                            "Stored assertion does not match its ID"
                        )
                    assertion = _decode_assertion(payload)
                    if (
                        assertion.kind.value != kind
                        or assertion.revision != bound_revision
                        or assertion.region not in coverage
                    ):
                        raise SnapshotIntegrityError(
                            "Stored assertion is incompatible with snapshot metadata"
                        )
                    assertions.append(assertion)
            except (TypeError, KeyError, json.JSONDecodeError) as error:
                raise SnapshotIntegrityError(
                    "Snapshot metadata cannot be decoded"
                ) from error
            if bound_revision.repository != self.repository:
                raise SnapshotIntegrityError(
                    "Snapshot belongs to a different repository"
                )
            return Snapshot(
                snapshot_id,
                bound_revision,
                coverage,
                tuple(assertions),
                observed_at,
            )

    def snapshot_ids(self, commit: str) -> tuple[str, ...]:
        """Find all published snapshots for a commit, most recently observed first."""
        validate_commit(commit)
        with closing(self._connect()) as db:
            self._check_identity(db)
            return tuple(
                row[0]
                for row in db.execute(
                    "SELECT id FROM snapshots WHERE json_extract(revision, '$.commit') = ? "
                    "ORDER BY observed_at DESC, id",
                    (commit,),
                )
            )
