"""Trusted local checkpoint storage and execution budget accounting."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from engine.execution.authority import ExecutionDenied
from engine.execution.envelope import ExecutionEnvelope


@dataclass(frozen=True)
class Checkpoint:
    status: str
    iterations: int
    tool_calls: int
    path: str | None
    oid: str | None
    reason: str | None


class CheckpointStore:
    """Store budgets and operation state in a database controlled by the host."""

    def __init__(self, path: Path) -> None:
        self._path = path
        with self._write() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS executions ("
                "id TEXT PRIMARY KEY, binding TEXT NOT NULL, started REAL NOT NULL, "
                "last_seen REAL NOT NULL, iterations INTEGER NOT NULL, calls INTEGER NOT NULL, "
                "status TEXT NOT NULL, path TEXT, oid TEXT, reason TEXT)"
            )

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            yield db

    def _get(
        self, db: sqlite3.Connection, envelope: ExecutionEnvelope
    ) -> sqlite3.Row | None:
        row = db.execute(
            "SELECT * FROM executions WHERE id = ?", (envelope.execution_id,)
        ).fetchone()
        if row is not None and row["binding"] != self._binding(envelope):
            raise ExecutionDenied("Execution identity is bound to a different envelope")
        return row

    @staticmethod
    def _binding(envelope: ExecutionEnvelope) -> str:
        payload = json.dumps(
            asdict(envelope), sort_keys=True, separators=(",", ":")
        ).encode()
        return sha256(payload).hexdigest()

    @staticmethod
    def _state(row: sqlite3.Row) -> Checkpoint:
        return Checkpoint(
            row["status"],
            row["iterations"],
            row["calls"],
            row["path"],
            row["oid"],
            row["reason"],
        )

    def load(self, envelope: ExecutionEnvelope) -> Checkpoint:
        with self._write() as db:
            if row := self._get(db, envelope):
                return self._state(row)
        raise ExecutionDenied("Execution checkpoint does not exist")

    def _exhausted(
        self,
        envelope: ExecutionEnvelope,
        row: sqlite3.Row,
        now: float,
        *,
        before_call: bool,
    ) -> bool:
        budget = envelope.budget
        return (
            now < row["last_seen"]
            or now - row["started"] >= budget.max_duration_seconds
            or (
                before_call
                and (
                    row["iterations"] >= budget.max_iterations
                    or row["calls"] >= budget.max_tool_calls
                )
            )
        )

    def reserve(self, envelope: ExecutionEnvelope, path: str, oid: str) -> Checkpoint:
        """Record the tool attempt before doing work. Each bounded read is one iteration."""
        now = datetime.now(UTC).timestamp()
        with self._write() as db:
            row = self._get(db, envelope)
            if row is None:
                db.execute(
                    "INSERT INTO executions VALUES (?, ?, ?, ?, 0, 0, 'ready', NULL, NULL, NULL)",
                    (envelope.execution_id, self._binding(envelope), now, now),
                )
                row = self._get(db, envelope)
                assert row is not None
            if row["status"] != "ready":
                raise ExecutionDenied(
                    "Execution requires explicit checkpoint resumption"
                )
            exhausted = self._exhausted(envelope, row, now, before_call=True)
            if exhausted:
                db.execute(
                    "UPDATE executions SET status = 'suspended', reason = 'budget' WHERE id = ?",
                    (envelope.execution_id,),
                )
            else:
                db.execute(
                    "UPDATE executions SET status = 'in_flight', path = ?, oid = ?, reason = NULL, "
                    "iterations = iterations + 1, calls = calls + 1, last_seen = ? WHERE id = ?",
                    (path, oid, now, envelope.execution_id),
                )
                reserved = Checkpoint(
                    "in_flight",
                    row["iterations"] + 1,
                    row["calls"] + 1,
                    path,
                    oid,
                    None,
                )
        if exhausted:
            raise ExecutionDenied("Execution budget is exhausted")
        return reserved

    def finish(
        self, envelope: ExecutionEnvelope, expected: Checkpoint, *, success: bool
    ) -> None:
        now = datetime.now(UTC).timestamp()
        with self._write() as db:
            row = self._get(db, envelope)
            if (
                row is None
                or row["status"] != "in_flight"
                or self._state(row) != expected
            ):
                raise ExecutionDenied(
                    "The tool attempt was superseded before completion"
                )
            expired = self._exhausted(envelope, row, now, before_call=False)
            reason = "budget" if expired else None if success else "tool_failure"
            db.execute(
                "UPDATE executions SET status = ?, reason = ?, last_seen = ? WHERE id = ?",
                (
                    "ready" if reason is None else "suspended",
                    reason,
                    max(now, row["last_seen"]),
                    envelope.execution_id,
                ),
            )
        if expired and success:
            raise ExecutionDenied("Execution deadline elapsed before completion")

    def resume(self, envelope: ExecutionEnvelope, expected: Checkpoint) -> None:
        """Record a separately revalidated resume without replaying the pending read."""
        now = datetime.now(UTC).timestamp()
        with self._write() as db:
            row = self._get(db, envelope)
            if (
                row is None
                or self._state(row) != expected
                or row["status"] not in ("in_flight", "suspended")
            ):
                raise ExecutionDenied("Checkpoint changed before resumption")
            if row["reason"] == "budget" or self._exhausted(
                envelope, row, now, before_call=True
            ):
                raise ExecutionDenied("Execution budget is exhausted")
            db.execute(
                "UPDATE executions SET status = 'ready', reason = NULL, last_seen = ? WHERE id = ?",
                (now, envelope.execution_id),
            )
