"""Refresh an immutable Project Brain snapshot against the current Git tree."""

from dataclasses import dataclass, replace

from engine.brain.discovery import (
    CODE_OBSERVATION,
    PROJECT_NOTE,
    inspect_code,
    project_notes,
)
from engine.brain.model import Assertion, KnowledgeKind
from engine.brain.retrieval import retrieve
from engine.brain.store import ProjectBrain, assertion_id
from engine.git.repository import GitRepository


@dataclass(frozen=True)
class Reconciliation:
    base_snapshot_id: str
    snapshot_id: str
    commit: str
    changed_paths: tuple[str, ...]
    refreshed: tuple[str, ...]
    removed: tuple[str, ...]
    needs_review: tuple[str, ...]


def _detected(item: Assertion) -> bool:
    return item.kind == KnowledgeKind.DERIVED and all(
        evidence.detail == CODE_OBSERVATION
        and evidence.reference.startswith("git:blob:")
        and evidence.path is not None
        for evidence in item.evidence
    )


def _key(item: Assertion) -> tuple[str, str, str, str]:
    return item.region, item.subject, item.relation, item.target


def reconcile(
    repository: GitRepository, brain: ProjectBrain, base_snapshot_id: str
) -> Reconciliation:
    """Publish HEAD knowledge while retaining the base snapshot for review."""
    head = repository.head_commit()
    if head is None:
        raise ValueError("Reconciliation requires a committed HEAD")
    base = brain.load(base_snapshot_id)
    if not base.regions:
        raise ValueError("Reconciliation requires a snapshot with recorded coverage")
    view = retrieve(repository, brain, base.id, target_commit=head)
    changed_regions = set(view.affected_regions)
    old_generated = {
        replace(item, revision=view.revision)
        for item in base.assertions
        if _detected(item) or item.relation == PROJECT_NOTE
    }
    generated = {
        *inspect_code(repository, view.revision, tuple(sorted(changed_regions))),
        *project_notes(repository, view.revision, base.regions[0]),
        *(
            replace(item, revision=view.revision)
            for item in view.current
            if _detected(item) and item.region not in changed_regions
        ),
    }
    retained = (
        replace(item, revision=view.revision)
        for item in view.current
        if not _detected(item) and item.relation != PROJECT_NOTE
    )
    if repository.head_commit() != head:
        raise ValueError(
            "HEAD changed during reconciliation; retry with the intended checkout"
        )
    snapshot = brain.publish_reconciliation(
        base, view.revision, (*retained, *generated)
    )
    new_keys = {_key(item) for item in generated}
    return Reconciliation(
        base.id,
        snapshot.id,
        head,
        view.changed_paths,
        tuple(sorted(assertion_id(item) for item in generated - old_generated)),
        tuple(
            sorted(
                assertion_id(item)
                for item in base.assertions
                if (_detected(item) or item.relation == PROJECT_NOTE)
                and _key(item) not in new_keys
            )
        ),
        tuple(
            sorted(
                assertion_id(item)
                for item in view.stale
                if not _detected(item) and item.relation != PROJECT_NOTE
            )
        ),
    )
