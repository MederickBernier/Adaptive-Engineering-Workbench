"""Explicit first-time discovery and a draft interview for maintainers."""

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

from engine.brain.discovery import inspect_revision
from engine.brain.model import (
    Assertion,
    Depth,
    Evidence,
    KnowledgeKind,
    Revision,
    Verification,
)
from engine.brain.store import ProjectBrain, _decode_assertion
from engine.git.repository import GitRepository


def scan_bootstrap(repository: GitRepository) -> dict[str, Any]:
    commit = repository.head_commit()
    if commit is None:
        raise ValueError("Bootstrap requires a committed revision")
    revision = Revision(repository.root.as_uri(), commit)
    observations = inspect_revision(repository, revision, (".",))
    facts = {item.relation for item in observations}
    questions = [
        {
            "id": "ownership",
            "topic": "Components",
            "prompt": "Which components own the main business rules, and where are their boundaries?",
        },
        {
            "id": "dependencies",
            "topic": "Components",
            "prompt": "Which runtime dependencies or external integrations matter most to maintainers?",
        },
        {
            "id": "constraints",
            "topic": "Conventions",
            "prompt": "Which repository conventions, sensitive areas, or architectural decisions should future tasks respect?",
        },
    ]
    if "test_tool" not in facts:
        questions.append(
            {
                "id": "tests",
                "topic": "Verification",
                "prompt": "Which commands or checks are authoritative for verifying changes?",
            }
        )
    if "build_system" not in facts:
        questions.append(
            {
                "id": "build",
                "topic": "Verification",
                "prompt": "How do maintainers build or run this project?",
            }
        )
    return {
        "state": "draft",
        "revision": asdict(revision),
        "regions": ["."],
        "observations": [asdict(item) for item in observations],
        "questions": questions,
        "limitations": [
            "Committed regular files only. Observations cover recognized signals; questions require maintainer input."
        ],
    }


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class BootstrapInterview:
    """Persist the draft and answers; publish only an explicitly reviewed revision."""

    def __init__(self, repository: GitRepository, brain: ProjectBrain) -> None:
        if repository.root.as_uri() != brain.repository:
            raise ValueError("Bootstrap database belongs to a different checkout")
        self.repository = repository
        self.brain = brain

    def start(self) -> dict[str, Any]:
        draft = scan_bootstrap(self.repository)
        identifier = uuid4().hex
        payload = _json({"draft": draft, "answers": {}})
        with self.brain._write() as db:
            db.execute(
                "INSERT INTO bootstrap_sessions VALUES (?, 1, ?, ?, NULL, NULL)",
                (identifier, draft["revision"]["commit"], payload),
            )
        return self.show(identifier)

    def _row(self, db: sqlite3.Connection, identifier: str) -> tuple:
        self.brain._check_identity(db)
        row = db.execute(
            "SELECT version, commit_id, payload, snapshot_id FROM bootstrap_sessions WHERE id = ?",
            (identifier,),
        ).fetchone()
        if row is None:
            raise ValueError("Unknown bootstrap session")
        return row

    @staticmethod
    def _digest(identifier: str, version: int, payload: str) -> str:
        return sha256(_json([identifier, version, payload]).encode()).hexdigest()

    def show(self, identifier: str) -> dict[str, Any]:
        with self.brain._write() as db:
            version, _, payload, snapshot_id = self._row(db, identifier)
        record = json.loads(payload)
        pending = [
            question["id"]
            for question in record["draft"]["questions"]
            if question["id"] not in record["answers"]
        ]
        return {
            "session_id": identifier,
            "version": version,
            **record,
            "pending_questions": pending,
            "review_digest": self._digest(identifier, version, payload),
            "state": "published"
            if snapshot_id
            else "interview"
            if pending
            else "ready_for_review",
            "snapshot_id": snapshot_id,
        }

    def answer(
        self,
        identifier: str,
        *,
        expected_version: int,
        question_id: str,
        maintainer: str,
        disposition: str,
        answer: str | None,
    ) -> dict[str, Any]:
        if not maintainer.strip() or len(maintainer) > 150:
            raise ValueError("A maintainer name of at most 150 characters is required")
        if disposition not in ("answered", "skipped", "deferred"):
            raise ValueError("Unknown interview disposition")
        if disposition == "answered":
            if not answer or not answer.strip() or len(answer.encode()) > 4096:
                raise ValueError(
                    "An answer requires nonempty text of at most 4096 bytes"
                )
        elif answer is not None:
            raise ValueError("Skipped and deferred questions cannot record an answer")
        with self.brain._write() as db:
            version, _, payload, snapshot_id = self._row(db, identifier)
            if snapshot_id or version != expected_version:
                raise ValueError(
                    "Bootstrap session is published or its version changed"
                )
            record = json.loads(payload)
            if question_id not in {item["id"] for item in record["draft"]["questions"]}:
                raise ValueError("Unknown bootstrap question")
            record["answers"][question_id] = {
                "disposition": disposition,
                "maintainer": maintainer.strip(),
                "answer": answer,
                "recorded_at": datetime.now(UTC).isoformat(),
            }
            db.execute(
                "UPDATE bootstrap_sessions SET payload = ?, version = version + 1 WHERE id = ?",
                (_json(record), identifier),
            )
        return self.show(identifier)

    def publish(self, identifier: str, *, review_digest: str) -> dict[str, Any]:
        with self.brain._write() as db:
            version, commit, payload, snapshot_id = self._row(db, identifier)
            if review_digest != self._digest(identifier, version, payload):
                raise ValueError("Bootstrap draft changed since review")
            if snapshot_id is None:
                if self.repository.head_commit() != commit:
                    raise ValueError(
                        "Checkout revision changed; start a new bootstrap review"
                    )
                record = json.loads(payload)
                draft, answers = record["draft"], record["answers"]
                if any(
                    question["id"] not in answers for question in draft["questions"]
                ):
                    raise ValueError(
                        "Answer, skip, or defer each question before publishing"
                    )
                revision = Revision(**draft["revision"])
                members = [
                    _decode_assertion(_json(item)) for item in draft["observations"]
                ]
                for question in draft["questions"]:
                    question_id = question["id"]
                    reply = answers[question_id]
                    if reply["disposition"] == "skipped":
                        continue
                    answered = reply["disposition"] == "answered"
                    evidence = Evidence(
                        f"bootstrap:{identifier}:{question_id}",
                        f"Reported by {reply['maintainer']} at {reply['recorded_at']}. Question: {question['prompt']}",
                    )
                    members.append(
                        Assertion(
                            revision,
                            "project",
                            f"maintainer_{question_id}"
                            if answered
                            else "maintainer_unresolved",
                            reply["answer"] if answered else question["prompt"],
                            (evidence,),
                            depth=Depth.STRUCTURAL,
                            kind=KnowledgeKind.DURABLE,
                            verification=Verification.VERIFIED
                            if answered
                            else Verification.PROVISIONAL,
                        )
                    )
                snapshot_id = self.brain._publish(
                    db, revision, tuple(draft["regions"]), members
                )
                db.execute(
                    "UPDATE bootstrap_sessions SET snapshot_id = ?, published_at = ? WHERE id = ?",
                    (snapshot_id, datetime.now(UTC).isoformat(), identifier),
                )
        return self.show(identifier)
