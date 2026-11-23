import sqlite3
from contextlib import closing
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from engine.brain.model import Assertion, Depth, Evidence, KnowledgeKind, Revision
from engine.brain.store import ProjectBrain

REVISION = Revision("example/project", "a" * 40, "master")


def claim() -> Assertion:
    return Assertion(
        REVISION,
        "service",
        "depends_on",
        "gateway",
        (Evidence("git:a:service.py", "Observed import", "service.py"),),
        depth=Depth.STRUCTURAL,
    )


def test_snapshots_reopen_with_explicit_members_and_provenance(tmp_path: Path) -> None:
    path = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(path, REVISION.repository)
    derived = claim()
    durable = replace(derived, relation="documents", kind=KnowledgeKind.DURABLE)
    first = brain.publish(REVISION, ["."], [derived])
    second = brain.publish(REVISION, ["."], [derived, durable])
    assert brain.publish(REVISION, ["."], [durable, derived, derived]) == second

    reopened = ProjectBrain(path, REVISION.repository)
    assert reopened.load(first.id).assertions == (derived,)
    assert set(reopened.load(second.id).assertions) == {derived, durable}
    assert first.id != second.id
    with pytest.raises(FrozenInstanceError):
        derived.target = "another gateway"  # type: ignore[misc]


def test_rejects_wrong_project_and_mixed_revisions(tmp_path: Path) -> None:
    path = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(path, REVISION.repository)
    with pytest.raises(ValueError, match="different repository"):
        ProjectBrain(path, "example/other")
    with pytest.raises(ValueError, match="revision does not match"):
        brain.publish(replace(REVISION, commit="b" * 40), ["."], [claim()])
    with pytest.raises(ValueError, match="outside snapshot coverage"):
        brain.publish(REVISION, ["src"], [claim()])


def test_failed_membership_write_rolls_back_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(path, REVISION.repository)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(
            "CREATE TRIGGER fail_membership BEFORE INSERT ON membership "
            "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="test failure"):
        brain.publish(REVISION, ["."], [claim()])
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("SELECT count(*) FROM snapshots").fetchone() == (0,)
        assert db.execute("SELECT count(*) FROM assertions").fetchone() == (0,)
