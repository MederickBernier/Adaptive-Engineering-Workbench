import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from engine.brain.model import Revision
from engine.brain.store import ProjectBrain
from engine.context.package import ContextPackage
from engine.planning.assessment import Level, PlanningError, Profile, assess
from engine.planning.history import PlanConflict, PlanHistory
from engine.planning.plan import Task, WorkUnit, build_plan


@pytest.mark.parametrize(
    ("inputs", "profile"),
    [
        ({"localized": True, "acceptance_clear": True}, Profile.QUICK),
        ({"localized": True}, Profile.STANDARD),
        ({"cross_cutting": True}, Profile.DEEP),
        (
            {"risk": Level.HIGH, "localized": True, "acceptance_clear": True},
            Profile.DEEP,
        ),
        ({"investigation_first": True}, Profile.EXPLORE),
        ({"uncertainty": Level.HIGH}, Profile.EXPLORE),
    ],
)
def test_profile_recommendation(inputs: dict, profile: Profile) -> None:
    assessment = assess(
        **({"risk": Level.LOW, "uncertainty": Level.LOW} | inputs),
        rationale="Observed task scope",
        evidence=("context:verified",),
    )
    assert assessment.profile == assessment.recommended == profile
    assert assessment.evidence == ("context:verified",)


def test_profile_override_preserves_recommendation_and_reason() -> None:
    assessment = assess(
        risk=Level.LOW,
        uncertainty=Level.LOW,
        rationale="Bounded change",
        requested=Profile.DEEP,
        override_reason="Engineer requests additional review",
    )
    assert assessment.recommended == Profile.STANDARD
    assert assessment.profile == Profile.DEEP
    assert "additional review" in assessment.rationale


def test_unresolved_exploration_cannot_be_overridden_into_implementation() -> None:
    with pytest.raises(PlanningError, match="resolve material uncertainty"):
        assess(
            risk=Level.MODERATE,
            uncertainty=Level.HIGH,
            rationale="Source behavior unknown",
            requested=Profile.QUICK,
            override_reason="Try a small change",
        )


@pytest.fixture
def task_schema() -> Draft202012Validator:
    path = Path(__file__).resolve().parents[2] / "contracts/task.schema.json"
    return Draft202012Validator(json.loads(path.read_bytes()))


def task() -> Task:
    return Task(
        "task-42",
        "example/project",
        "Handle empty search",
        ("Empty queries return no results.",),
    )


def test_quick_plan_exports_one_work_unit_without_publication_authority(
    task_schema,
) -> None:
    assessment = assess(
        risk=Level.LOW,
        uncertainty=Level.LOW,
        localized=True,
        acceptance_clear=True,
        rationale="Existing search contract covers this case",
    )
    draft = build_plan(
        task(),
        assessment,
        approach="Reuse the empty-result path",
        scope=("src/search.py",),
        verification=("Run the search tests",),
    )
    document = draft.to_task_document()
    task_schema.validate(document)
    assert [unit.id for unit in draft.work_units] == ["task-42-01"]
    assert document["approval"]["required_actions"] == ["implement", "run_tests"]
    assert document["approval"]["status"] == "pending"
    assert "grant_id" not in document["approval"]
    assert document["plan"]["revision"] == 1


def unit(identifier: str, scope: str, dependencies: tuple[str, ...] = ()) -> WorkUnit:
    return WorkUnit(
        identifier,
        f"Update {identifier}",
        (scope,),
        ("Review output",),
        ("Run targeted tests",),
        dependencies,
    )


def test_deep_plan_orders_engineering_units_by_dependencies(task_schema) -> None:
    assessment = assess(
        risk=Level.HIGH, uncertainty=Level.LOW, rationale="Crosses a data boundary"
    )
    core = unit("core", "src/core.py")
    tests = unit("tests", "tests/", ("core",))
    draft = build_plan(
        task(),
        assessment,
        approach="Change the boundary and then verify its consumers.",
        scope=("src/**", "tests/**"),
        work_units=(tests, core),
        create_branch=True,
    )
    task_schema.validate(draft.to_task_document())
    assert draft.work_units == (core, tests)
    assert draft.checkpoints[0].action == "create_branch"
    assert draft.checkpoints[-1].work_unit_id == "tests"


@pytest.mark.parametrize(
    ("units", "message"),
    [
        ((unit("one", "src/file.py", ("missing",)),), "Unknown Work Unit dependency"),
        (
            (
                unit("one", "src/file.py", ("two",)),
                unit("two", "src/other.py", ("one",)),
            ),
            "contain a cycle",
        ),
        (
            (unit("one", "src/file.py"), unit("one", "src/other.py")),
            "Duplicate Work Unit ID",
        ),
        ((unit("one", "src-similar/file.py"),), "scope exceeds"),
    ],
)
def test_plan_rejects_invalid_dependency_or_scope(units, message) -> None:
    assessment = assess(
        risk=Level.MODERATE, uncertainty=Level.LOW, rationale="Bounded maintenance"
    )
    with pytest.raises(PlanningError, match=message):
        build_plan(
            task(),
            assessment,
            approach="Update search",
            scope=("src/**",),
            work_units=units,
        )


def test_explore_is_read_only_and_requests_no_implementation_or_commit(
    task_schema,
) -> None:
    assessment = assess(
        risk=Level.MODERATE, uncertainty=Level.HIGH, rationale="Behavior is unknown"
    )
    options = {
        "approach": "Inspect callers",
        "scope": ("src/**",),
        "verification": ("Stop after documenting search callers",),
        "review_questions": ("Which component owns empty search behavior?",),
        "investigation_budget": 20,
    }
    draft = build_plan(task(), assessment, **options)
    document = draft.to_task_document()
    task_schema.validate(document)
    assert document["approval"]["required_actions"] == ["investigate"]
    assert document["plan"]["work_units"] == []
    assert draft.investigation_budget == 20
    with pytest.raises(PlanningError, match="cannot propose"):
        build_plan(
            task(), assessment, work_units=(unit("one", "src/file.py"),), **options
        )


def test_plan_rejects_context_for_a_different_task() -> None:
    context = ContextPackage.create(
        {
            "schema_version": "0.1",
            "identity": {
                "task_id": "different-task",
                "repository": "example/project",
                "revision": {
                    "branch": "master",
                    "commit": "a" * 40,
                    "snapshot_id": "snapshot",
                },
            },
            "integrity": {
                "freshness": "current",
                "coverage": "partial",
                "limitations": [],
            },
        }
    )
    assessment = assess(risk=Level.LOW, uncertainty=Level.LOW, rationale="Bounded task")
    with pytest.raises(PlanningError, match="different task or repository"):
        build_plan(task(), assessment, approach="Inspect callers", context=context)


def quick_draft(
    scope: str = "src/search.py", *, rationale: str = "Established contract"
):
    return build_plan(
        task(),
        assess(
            risk=Level.LOW,
            uncertainty=Level.LOW,
            localized=True,
            acceptance_clear=True,
            rationale=rationale,
        ),
        approach="Reuse existing behavior",
        scope=(scope,),
        verification=("Run search tests",),
    )


def test_plan_history_preserves_revisions_and_classifies_edits(
    tmp_path: Path, task_schema
) -> None:
    path = tmp_path / "brain.sqlite3"
    history = PlanHistory(ProjectBrain(path, task().repository))
    first = history.append(quick_draft())
    assert history.append(quick_draft()) == first

    spelling = history.append(
        quick_draft(rationale="Established search contract"), expected_revision=1
    )
    assert spelling.previous_revision == 1
    assert spelling.material_changes == ()
    assert not spelling.approval_reassessment_required

    expanded = history.append(
        quick_draft("src/**", rationale="Established search contract"),
        expected_revision=2,
    )
    assert {"scope", "work_units", "approval_checkpoints"} <= set(
        expanded.material_changes
    )
    assert expanded.approval_reassessment_required
    assert expanded.plan_id == first.plan_id
    reopened = PlanHistory(ProjectBrain(path, task().repository))
    assert reopened.load(first.plan_id, 1) == first
    record = reopened.load(first.plan_id, 3).to_record()
    task_schema.validate(record["task_document"])
    assert record["task_document"]["approval"]["status"] == "pending"
    assert "grant_id" not in record["task_document"]["approval"]
    assert record["task_document"]["plan"]["revision"] == 3
    with pytest.raises(PlanConflict, match="Expected plan revision 1, found 3"):
        history.append(quick_draft("other.py"), expected_revision=1)


def test_concurrent_plan_appends_require_a_current_predecessor(tmp_path: Path) -> None:
    history = PlanHistory(ProjectBrain(tmp_path / "brain.sqlite3", task().repository))
    first = history.append(quick_draft())

    def append(scope: str) -> str:
        try:
            return str(history.append(quick_draft(scope), expected_revision=1).revision)
        except PlanConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(append, ["src/one.py", "src/two.py"])) == [
            "2",
            "conflict",
        ]
    assert history.load(first.plan_id, 1) == first


def test_plan_history_migrates_existing_project_brain(tmp_path: Path) -> None:
    path = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(path, task().repository)
    original = brain.publish(Revision(brain.repository, "a" * 40), (".",), ())
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("DROP TABLE plan_revisions")
        db.execute("DROP TABLE discovery_cache")
        db.execute("DROP TABLE bootstrap_sessions")
        db.execute("PRAGMA user_version = 1")
    migrated = ProjectBrain(path, brain.repository)
    assert migrated.load(original.id) == original
    assert PlanHistory(migrated).append(quick_draft()).revision == 1
    with pytest.raises(PlanningError, match="does not match"):
        PlanHistory(migrated).append(
            replace(quick_draft(), task=replace(task(), repository="elsewhere"))
        )
