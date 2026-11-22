
"""
AEW local Git preflight coordinator.

Implements the local inspection portion of:
- ADR-004: Workspace Consistency
- ADR-005: Branch Preflight and Naming

This module is read-only.

It does not:
- Fetch remotes.
- Create or switch branches.
- Stage or commit changes.
- Inspect GitHub pull requests.
- Authorize implementation.

A successful local assessment is not equivalent to
a completed repository-wide preflight.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

from engine.config import AEWConfig
from engine.git.repository import (
    GitFileStatus,
    GitRepository,
    WorkspaceState,
)


class PreflightStatus(str, Enum):
    """Outcome of local preflight assessment."""

    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


class OverlapStatus(str, Enum):
    """Relationship between workspace changes and task scope."""

    NONE = "none"
    NON_OVERLAPPING = "non_overlapping"
    OVERLAPPING = "overlapping"
    UNKNOWN = "unknown"


class FindingSeverity(str, Enum):
    """Severity of a preflight finding."""

    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


@dataclass(frozen=True)
class PreflightFinding:
    """One evidence-backed local preflight finding."""

    code: str
    severity: FindingSeverity
    message: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkspaceAssessment:
    """Workspace status relative to the intended scope."""

    state: WorkspaceState
    overlap: OverlapStatus
    changed_paths: tuple[str, ...]
    overlapping_paths: tuple[str, ...]


@dataclass(frozen=True)
class LocalPreflightReport:
    """Immutable local preflight observation."""

    repository: Path
    branch: str | None
    head_commit: str | None
    integration_branch: str
    integration_commit: str | None
    proposed_branch: str | None
    branch_collision: bool | None
    workspace: WorkspaceAssessment
    findings: tuple[PreflightFinding, ...]
    status: PreflightStatus

    # Local inspection never establishes remote freshness
    # or PR coordination completeness.
    remote_freshness_verified: bool = False
    pull_requests_checked: bool = False


def _normalize_path(path: str) -> str:
    """
    Normalize a repository-relative path for comparison.

    This is only a lexical normalization helper.
    It is not a filesystem authorization boundary.
    """

    return path.replace("\\", "/").removeprefix("./")


def _path_matches_scope(
    path: str,
    scope: str,
) -> bool:
    """
    Match a path against a simple task-scope expression.

    Supported forms:
        src/customer/CustomerMapper.java
        src/customer/**
        src/customer/

    This intentionally does not implement arbitrary glob
    patterns or filesystem security enforcement.
    """

    path = _normalize_path(path)
    scope = _normalize_path(scope)

    if scope.endswith("/**"):
        prefix = scope[:-3].rstrip("/")
        return path == prefix or path.startswith(
            prefix + "/"
        )

    if scope.endswith("/"):
        return path.startswith(scope)

    return path == scope


def assess_workspace(
    changes: Sequence[GitFileStatus],
    intended_scope: Sequence[str],
) -> WorkspaceAssessment:
    """
    Compare Git changes with the intended task scope.

    This is a conservative local overlap assessment.

    Unsupported scope patterns produce UNKNOWN rather
    than being interpreted as non-overlapping.
    """

    changed_paths: set[str] = set()

    for change in changes:
        changed_paths.add(
            _normalize_path(change.path)
        )

        if change.original_path:
            changed_paths.add(
                _normalize_path(change.original_path)
            )

    if not changes:
        return WorkspaceAssessment(
            state=WorkspaceState.CLEAN,
            overlap=OverlapStatus.NONE,
            changed_paths=(),
            overlapping_paths=(),
        )

    if not intended_scope:
        return WorkspaceAssessment(
            state=WorkspaceState.DIRTY,
            overlap=OverlapStatus.UNKNOWN,
            changed_paths=tuple(sorted(changed_paths)),
            overlapping_paths=(),
        )

    unsupported = any(
        "*" in scope
        and not scope.endswith("/**")
        for scope in intended_scope
    )

    if unsupported:
        return WorkspaceAssessment(
            state=WorkspaceState.DIRTY,
            overlap=OverlapStatus.UNKNOWN,
            changed_paths=tuple(sorted(changed_paths)),
            overlapping_paths=(),
        )

    overlapping = {
        path
        for path in changed_paths
        if any(
            _path_matches_scope(path, scope)
            for scope in intended_scope
        )
    }

    if overlapping:
        overlap = OverlapStatus.OVERLAPPING
    else:
        overlap = OverlapStatus.NON_OVERLAPPING

    return WorkspaceAssessment(
        state=WorkspaceState.DIRTY,
        overlap=overlap,
        changed_paths=tuple(sorted(changed_paths)),
        overlapping_paths=tuple(sorted(overlapping)),
    )


class GitPreflight:
    """Coordinate local, read-only Git preflight checks."""

    def __init__(
        self,
        repository: GitRepository,
        config: AEWConfig,
    ) -> None:
        self._repository = repository
        self._config = config

    def inspect(
        self,
        *,
        task_type: str,
        issue: str,
        title: str,
        intended_scope: Sequence[str],
        remote: str = "origin",
    ) -> LocalPreflightReport:
        """Build a local preflight report."""

        snapshot = self._repository.snapshot()

        workspace = assess_workspace(
            snapshot.changes,
            intended_scope,
        )

        findings: list[PreflightFinding] = []

        if snapshot.head_commit is None:
            findings.append(
                PreflightFinding(
                    code="GIT_UNBORN_HEAD",
                    severity=FindingSeverity.BLOCKING,
                    message=(
                        "Repository has no HEAD commit. "
                        "A verified integration baseline "
                        "cannot be established."
                    ),
                )
            )

        if snapshot.detached:
            findings.append(
                PreflightFinding(
                    code="GIT_DETACHED_HEAD",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "Repository is in detached HEAD state."
                    ),
                )
            )

        if workspace.overlap == OverlapStatus.OVERLAPPING:
            findings.append(
                PreflightFinding(
                    code="WORKSPACE_OVERLAP",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "Existing workspace changes overlap "
                        "the intended task scope."
                    ),
                    evidence=workspace.overlapping_paths,
                )
            )

        elif workspace.overlap == OverlapStatus.UNKNOWN:
            findings.append(
                PreflightFinding(
                    code="WORKSPACE_SCOPE_UNKNOWN",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "Workspace overlap cannot be "
                        "determined from the supplied scope."
                    ),
                    evidence=workspace.changed_paths,
                )
            )

        elif workspace.overlap == OverlapStatus.NON_OVERLAPPING:
            findings.append(
                PreflightFinding(
                    code="WORKSPACE_NON_OVERLAPPING",
                    severity=FindingSeverity.INFO,
                    message=(
                        "Existing workspace changes appear "
                        "outside the intended task scope."
                    ),
                    evidence=workspace.changed_paths,
                )
            )

        integration_branch = (
            self._config.integration_branch
        )

        integration_commit = (
            self._repository.integration_branch_commit(
                integration_branch,
                remote=remote,
            )
        )

        if integration_commit is None:
            findings.append(
                PreflightFinding(
                    code="INTEGRATION_BASELINE_UNAVAILABLE",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "The configured integration branch "
                        "has no locally known remote-tracking "
                        "commit. Remote freshness is unknown."
                    ),
                    evidence=(
                        f"{remote}/{integration_branch}",
                    ),
                )
            )

        proposed_branch: str | None = None
        branch_collision: bool | None = None

        try:
            candidate = (
                self._config.generate_branch_name(
                    task_type=task_type,
                    issue=issue,
                    title=title,
                )
            )

            if not self._repository.is_valid_branch_name(
                candidate
            ):
                findings.append(
                    PreflightFinding(
                        code="INVALID_BRANCH_NAME",
                        severity=FindingSeverity.BLOCKING,
                        message=(
                            "Generated branch name does not "
                            "satisfy Git reference rules."
                        ),
                        evidence=(candidate,),
                    )
                )
            else:
                proposed_branch = candidate

                branch_collision = (
                    self._repository.branch_exists(
                        candidate,
                        remote=remote,
                    )
                )

                if branch_collision:
                    findings.append(
                        PreflightFinding(
                            code="BRANCH_COLLISION",
                            severity=FindingSeverity.BLOCKING,
                            message=(
                                "Proposed task branch already "
                                "exists in known Git references."
                            ),
                            evidence=(candidate,),
                        )
                    )

        except ValueError as error:
            findings.append(
                PreflightFinding(
                    code="BRANCH_GENERATION_FAILED",
                    severity=FindingSeverity.BLOCKING,
                    message=str(error),
                )
            )

        findings.append(
            PreflightFinding(
                code="REMOTE_FRESHNESS_NOT_VERIFIED",
                severity=FindingSeverity.WARNING,
                message=(
                    "Local preflight does not fetch remote "
                    "references or verify integration "
                    "branch freshness."
                ),
            )
        )

        findings.append(
            PreflightFinding(
                code="PR_PREFLIGHT_NOT_PERFORMED",
                severity=FindingSeverity.WARNING,
                message=(
                    "Active pull requests and concurrent "
                    "branch dependencies have not been "
                    "inspected."
                ),
            )
        )

        if any(
            finding.severity == FindingSeverity.BLOCKING
            for finding in findings
        ):
            status = PreflightStatus.BLOCKED
        else:
            status = PreflightStatus.UNAVAILABLE

        return LocalPreflightReport(
            repository=snapshot.root,
            branch=snapshot.branch,
            head_commit=snapshot.head_commit,
            integration_branch=integration_branch,
            integration_commit=integration_commit,
            proposed_branch=proposed_branch,
            branch_collision=branch_collision,
            workspace=workspace,
            findings=tuple(findings),
            status=status,
        )
