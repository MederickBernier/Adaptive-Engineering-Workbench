"""Select and seal bounded engineering context from Project Brain evidence."""

from dataclasses import dataclass
from typing import Any

from engine.brain.model import Assertion, Depth, Verification
from engine.brain.retrieval import retrieve
from engine.brain.store import ProjectBrain, assertion_id
from engine.context.package import ContextPackage, ContextPackageError
from engine.git.preflight import FindingSeverity, LocalPreflightReport
from engine.git.repository import GitRepository, WorkspaceState

_DEPTH = {
    Depth.DISCOVERY: "light",
    Depth.STRUCTURAL: "standard",
    Depth.BEHAVIORAL: "deep",
    Depth.SEMANTIC: "deep",
}
_DEPTH_ORDER = {depth: rank for rank, depth in enumerate(Depth)}
_BUDGET_LIMITATION = "Some relevant assertions were omitted to fit the package budget."


@dataclass(frozen=True)
class _Selection:
    assertion: Assertion
    stale: bool
    relevance: str

    def sort_key(self) -> tuple[bool, bool, bool, int, str]:
        return (
            self.stale,
            self.relevance != "direct",
            self.assertion.verification != Verification.VERIFIED,
            -_DEPTH_ORDER[self.assertion.depth],
            assertion_id(self.assertion),
        )


def _assertion_entry(selection: _Selection) -> dict[str, Any]:
    item = selection.assertion
    evidence = [
        {
            "source": "repository" if source.reference.startswith("git:") else "manual",
            "reference": source.reference,
            "revision": item.revision.commit,
            "description": (
                f"{source.detail} (depth: {item.depth.value}, verification: {item.verification.value})"
                + (f" (path: {source.path})" if source.path is not None else "")
            ),
        }
        for source in item.evidence
    ]
    verification = (
        "source_verified"
        if item.verification == Verification.VERIFIED
        else "provisional"
    )
    return {
        "id": assertion_id(item),
        "claim": f"{item.subject} {item.relation} {item.target}",
        "relevance": selection.relevance,
        "authority": "informational",
        "verification": "stale" if selection.stale else verification,
        "evidence": evidence,
    }


def _knowledge(selections: list[_Selection]) -> tuple[dict[str, Any], dict[str, Any]]:
    knowledge: dict[str, list] = {"components": [], "contracts": [], "assertions": []}
    project: dict[str, list] = {
        "languages": [],
        "frameworks": [],
        "conventions": [],
        "verification_commands": [],
    }
    components: set[tuple[str, str]] = set()
    for selection in selections:
        item = selection.assertion
        entry = _assertion_entry(selection)
        knowledge["assertions"].append(entry)
        if selection.stale or item.verification != Verification.VERIFIED:
            continue
        component = (item.subject, item.region)
        if component not in components:
            components.add(component)
            knowledge["components"].append(
                {
                    "id": entry["id"],
                    "label": item.subject,
                    "scope": [item.region],
                    "depth": _DEPTH[item.depth],
                }
            )
        if item.relation in ("language", "framework"):
            project[item.relation + "s"].append(item.target)
        if item.relation in ("contract", "format_convention", "convention_file"):
            reference = {
                "id": entry["id"],
                "authority": entry["authority"],
                "scope": [item.region],
                "evidence": entry["evidence"],
            }
            if item.relation == "contract":
                knowledge["contracts"].append(reference)
            else:
                project["conventions"].append(reference)
        if item.relation == "verification_command":
            project["verification_commands"].append(
                {
                    "command": item.target,
                    "evidence": entry["evidence"][0],
                }
            )
    for field in ("languages", "frameworks"):
        project[field] = sorted(set(project[field]))
    return knowledge, project


def _coordination(report: LocalPreflightReport) -> dict[str, Any]:
    relevant = []
    for pr in report.pull_requests:
        findings = [
            finding for finding in report.findings if pr.url in finding.evidence
        ]
        if findings:
            relevant.append(
                {
                    "number": pr.number,
                    "severity": "blocking"
                    if any(
                        finding.severity == FindingSeverity.BLOCKING
                        for finding in findings
                    )
                    else "potential",
                    "reason": " ".join(
                        dict.fromkeys(finding.message for finding in findings)
                    ),
                }
            )
    return {"relevant_prs": sorted(relevant, key=lambda item: item["number"])}


def assemble_context(
    repository: GitRepository,
    brain: ProjectBrain,
    snapshot_id: str,
    *,
    task_id: str,
    branch: str,
    commit: str,
    region: str,
    max_bytes: int = 16_384,
    reconcile: bool = False,
    workspace_fingerprint: str | None = None,
    preflight: LocalPreflightReport | None = None,
) -> ContextPackage:
    """Seal a scoped package, optionally reconciling the snapshot to a different commit."""
    if max_bytes < 1:
        raise ContextPackageError("Context Package byte budget must be positive")
    snapshot = brain.load(snapshot_id)
    if commit != snapshot.revision.commit and not reconcile:
        raise ContextPackageError(
            "Context commit differs from the snapshot; explicit reconciliation is required"
        )
    if not repository.has_commit(commit):
        raise ContextPackageError("Context commit is unavailable locally")
    if workspace_fingerprint is not None and not workspace_fingerprint.strip():
        raise ContextPackageError("Workspace fingerprint must be nonempty")

    limitations = [
        f"Selected region: {region}.",
        "Knowledge coverage is limited to observed evidence.",
    ]
    if workspace_fingerprint is not None:
        limitations.append(
            "The workspace fingerprint was supplied by the caller. Knowledge was selected from committed revisions."
        )
    uncertainties = []
    if preflight is not None:
        if (
            preflight.repository != repository.root
            or preflight.head_commit != commit
            or preflight.branch != branch
        ):
            raise ContextPackageError(
                "Preflight evidence does not match the package repository, commit, and branch"
            )
        if (
            preflight.workspace.state == WorkspaceState.DIRTY
            and workspace_fingerprint is None
        ):
            raise ContextPackageError(
                "Dirty preflight evidence requires a workspace fingerprint"
            )
    if preflight is None or not preflight.pull_requests_checked:
        uncertainties.append(
            {
                "id": "coordination-unavailable",
                "question": "What active pull requests affect this task?",
                "blocking": False,
                "reason": "Complete pull request coordination evidence was unavailable.",
            }
        )
    if commit != snapshot.revision.commit:
        limitations.append(
            f"Snapshot {snapshot.id} was reconciled from {snapshot.revision.commit} to {commit}."
        )

    view = retrieve(repository, brain, snapshot_id, target_commit=commit, region=region)
    if not view.covered_regions:
        limitations.append(
            "The selected region is outside the recorded snapshot coverage."
        )
    candidates = [
        *(_Selection(item, False, "direct") for item in view.current),
        *(_Selection(item, True, "direct") for item in view.stale),
    ]
    dependencies = {
        entry.assertion.target
        for entry in candidates
        if not entry.stale and entry.assertion.relation == "depends_on"
    }
    if dependencies:
        full_view = retrieve(repository, brain, snapshot_id, target_commit=commit)
        already_selected = {item.assertion for item in candidates}
        candidates.extend(
            _Selection(item, stale, "related")
            for items, stale in ((full_view.current, False), (full_view.stale, True))
            for item in items
            if item.subject in dependencies and item not in already_selected
        )
    candidates.sort(key=_Selection.sort_key)

    def seal(selected: list[_Selection], *, truncated: bool) -> ContextPackage:
        knowledge, project = _knowledge(selected)
        depths = {item.assertion.depth for item in selected}
        return ContextPackage.create(
            {
                "schema_version": "0.1",
                "identity": {
                    "task_id": task_id,
                    "repository": view.revision.repository,
                    "revision": {
                        "branch": branch,
                        "commit": commit,
                        "snapshot_id": snapshot_id,
                        "workspace_fingerprint": workspace_fingerprint,
                    },
                },
                "integrity": {
                    "freshness": "stale"
                    if any(item.stale for item in selected)
                    else "current"
                    if selected
                    else "unknown",
                    "coverage": "partial" if view.covered_regions else "unknown",
                    "discovery_depth": "mixed"
                    if len(depths) > 1
                    else _DEPTH[next(iter(depths))]
                    if depths
                    else "unknown",
                    "limitations": [*limitations, _BUDGET_LIMITATION]
                    if truncated
                    else limitations,
                },
                "knowledge": knowledge,
                "project": project,
                "uncertainties": uncertainties,
                **(
                    {"coordination": _coordination(preflight)}
                    if preflight is not None
                    else {}
                ),
            }
        )

    complete = seal(candidates, truncated=False)
    if len(complete.to_json()) <= max_bytes:
        return complete
    selected: list[_Selection] = []
    bounded = seal(selected, truncated=True)
    if len(bounded.to_json()) > max_bytes:
        raise ContextPackageError(
            "Context Package byte budget is smaller than required metadata"
        )
    for candidate in candidates:
        trial = seal([*selected, candidate], truncated=True)
        if len(trial.to_json()) <= max_bytes:
            selected.append(candidate)
            bounded = trial
    return bounded
