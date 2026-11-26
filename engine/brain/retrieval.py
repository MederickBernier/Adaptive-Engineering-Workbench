"""Retrieve historical knowledge and evaluate its applicability to a committed revision."""

from dataclasses import dataclass

from engine.brain.model import Assertion, Depth, KnowledgeKind, Revision, validate_path
from engine.brain.store import ProjectBrain
from engine.git.repository import GitRepository


@dataclass(frozen=True)
class KnowledgeView:
    snapshot_id: str
    revision: Revision
    covered_regions: tuple[str, ...]
    affected_regions: tuple[str, ...]
    changed_paths: tuple[str, ...]
    current: tuple[Assertion, ...]
    stale: tuple[Assertion, ...]


def _within(path: str, region: str) -> bool:
    return region == "." or path == region or path.startswith(region + "/")


def _touches(left: str, right: str) -> bool:
    return _within(left, right) or _within(right, left)


def _affected(
    assertions: tuple[Assertion, ...],
    regions: tuple[str, ...],
    changes: tuple[str, ...],
) -> set[Assertion]:
    invalid = set()
    affected_regions = {
        region
        for region in regions
        if any(_touches(change, region) for change in changes)
    }
    for item in assertions:
        paths = tuple(
            evidence.path for evidence in item.evidence if evidence.path is not None
        )
        if (
            (changes and item.relation.startswith("maintainer_"))
            or any(_touches(change, path) for change in changes for path in paths)
            or (
                item.kind == KnowledgeKind.DERIVED
                and item.region in affected_regions
                and (item.depth != Depth.DISCOVERY or not paths)
            )
        ):
            invalid.add(item)

    dependencies: dict[str, set[str]] = {}
    for item in assertions:
        if item.relation == "depends_on":
            dependencies.setdefault(item.subject, set()).add(item.target)
    affected_subjects = affected_regions | {item.subject for item in invalid}
    while True:
        dependent_subjects = {
            subject
            for subject, targets in dependencies.items()
            if targets & affected_subjects
        } - affected_subjects
        if not dependent_subjects:
            break
        affected_subjects.update(dependent_subjects)
    invalid.update(
        item
        for item in assertions
        if item.kind == KnowledgeKind.DERIVED
        and dependencies.get(item.subject, set()) & affected_subjects
    )
    return invalid


def retrieve(
    repository: GitRepository,
    brain: ProjectBrain,
    snapshot_id: str,
    *,
    target_commit: str | None = None,
    region: str = ".",
) -> KnowledgeView:
    """Reconcile on demand using a Git tree diff and explicit dependency claims."""
    if brain.repository != repository.root.as_uri():
        raise ValueError("Project Brain identity does not match the Git checkout")
    if region != ".":
        validate_path(region)
    snapshot = brain.load(snapshot_id)
    revision = snapshot.revision
    if target_commit is not None and target_commit != revision.commit:
        revision = Revision(revision.repository, target_commit)
        changes = repository.changed_paths_between(
            snapshot.revision.commit, revision.commit
        )
    else:
        changes = ()

    affected = _affected(snapshot.assertions, snapshot.regions, changes)
    selected = tuple(
        item
        for item in snapshot.assertions
        if _within(item.region, region)
        or (
            item.region == "."
            and item.kind == KnowledgeKind.DURABLE
            and item.relation.startswith("maintainer_")
        )
        or any(
            evidence.path is not None and _touches(evidence.path, region)
            for evidence in item.evidence
        )
    )
    coverage = tuple(area for area in snapshot.regions if _touches(area, region))
    stale_regions = {item.region for item in selected if item in affected}
    affected_coverage = tuple(
        area
        for area in coverage
        if area in stale_regions or any(_touches(path, area) for path in changes)
    )
    return KnowledgeView(
        snapshot_id,
        revision,
        coverage,
        affected_coverage,
        changes,
        tuple(item for item in selected if item not in affected),
        tuple(item for item in selected if item in affected),
    )
