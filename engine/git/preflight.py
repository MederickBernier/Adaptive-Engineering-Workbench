"""
AEW Git preflight coordinator.

Implements the local inspection portion of:
- ADR-004: Workspace Consistency
- ADR-005: Branch Preflight and Naming

Version: 0.1.1

This module is read-only.

It does not:
- Fetch remotes.
- Create or switch branches.
- Stage or commit changes.
- Authorize implementation.

Local inspection is the default. Optional remote baseline verification observes
the configured integration ref and checks for its commit in the local object
store. An optional GitHub client adds pull request coordination evidence.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from engine.config import AEWConfig, ConfigurationError
from engine.git.repository import (
    GitError,
    GitFileStatus,
    GitRepository,
    WorkspaceState,
)
from engine.github.client import GitHubClient, GitHubError, GitHubPullRequest


class PreflightStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


class OverlapStatus(str, Enum):
    NONE = "none"
    NON_OVERLAPPING = "non_overlapping"
    OVERLAPPING = "overlapping"
    UNKNOWN = "unknown"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


@dataclass(frozen=True)
class PreflightFinding:
    code: str
    severity: FindingSeverity
    message: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkspaceAssessment:
    state: WorkspaceState
    overlap: OverlapStatus
    changed_paths: tuple[str, ...]
    overlapping_paths: tuple[str, ...]


@dataclass(frozen=True)
class IntegrationBaseline:
    remote: str
    branch: str
    tracking_commit: str | None
    local_commit: str | None
    remote_commit: str | None
    observed_at: datetime | None
    object_available: bool | None


@dataclass(frozen=True)
class LocalPreflightReport:
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

    # The observed remote HEAD matches the tracking ref and exists locally.
    remote_freshness_verified: bool = False
    pull_requests_checked: bool = False
    baseline: IntegrationBaseline | None = None
    pull_requests: tuple[GitHubPullRequest, ...] = ()
    remote_branch_collision: bool | None = None
    intended_scope: tuple[str, ...] = ()


class ScopeKind(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    RECURSIVE = "recursive"


@dataclass(frozen=True)
class ScopeExpression:
    """
    Parsed repository-relative scope expression.

    Supported forms:
        src/customer/CustomerMapper.java
        src/customer/
        src/customer/**

    No general glob support is implied.
    """

    path: str
    kind: ScopeKind

    def matches(self, candidate: str) -> bool:
        if self.kind == ScopeKind.FILE:
            return candidate == self.path

        if self.kind == ScopeKind.DIRECTORY:
            return candidate.startswith(self.path + "/")

        return candidate == self.path or candidate.startswith(self.path + "/")

    def contains(self, child: ScopeExpression) -> bool:
        if child.kind == ScopeKind.FILE:
            return self.matches(child.path)
        if self.kind == ScopeKind.FILE:
            return False
        if self.path == child.path:
            return self.kind == ScopeKind.RECURSIVE or child.kind == ScopeKind.DIRECTORY
        return child.path.startswith(self.path + "/")


class ScopeSyntaxError(ValueError):
    """Raised when a scope expression is unsupported."""


_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_GLOB_CHARACTERS = frozenset("*?[]{}")


def _validate_relative_path(
    path: str,
    *,
    allow_trailing_slash: bool,
) -> str:
    """
    Validate a lexical repository-relative path.

    This does not resolve symlinks and must not be
    used for filesystem write authorization.
    """

    if not isinstance(path, str) or not path:
        raise ScopeSyntaxError("Scope path cannot be empty")

    if "\x00" in path:
        raise ScopeSyntaxError("NUL characters are not permitted")

    if "\\" in path:
        raise ScopeSyntaxError("Backslashes are not supported in scope paths")

    if path.startswith("/") or _DRIVE_PREFIX.match(path):
        raise ScopeSyntaxError("Absolute paths are not supported")

    normalized = path

    if allow_trailing_slash:
        normalized = normalized.rstrip("/")

    if not normalized:
        raise ScopeSyntaxError("Scope path cannot reference repository root")

    segments = normalized.split("/")

    if any(segment in ("", ".", "..") for segment in segments):
        raise ScopeSyntaxError(
            "Empty, current, or parent path segments are not permitted"
        )

    if any(
        character in segment for segment in segments for character in _GLOB_CHARACTERS
    ):
        raise ScopeSyntaxError("Unsupported glob expression")

    return normalized


def parse_scope(expression: str) -> ScopeExpression:
    """
    Parse one supported scope expression.

    Fail closed for unsupported patterns.
    """

    if not isinstance(expression, str):
        raise ScopeSyntaxError("Scope expression must be a string")

    if expression.endswith("/**"):
        path = _validate_relative_path(
            expression[:-3],
            allow_trailing_slash=False,
        )

        return ScopeExpression(
            path=path,
            kind=ScopeKind.RECURSIVE,
        )

    if expression.endswith("/"):
        path = _validate_relative_path(
            expression,
            allow_trailing_slash=True,
        )

        return ScopeExpression(
            path=path,
            kind=ScopeKind.DIRECTORY,
        )

    path = _validate_relative_path(
        expression,
        allow_trailing_slash=False,
    )

    return ScopeExpression(
        path=path,
        kind=ScopeKind.FILE,
    )


def _normalize_changed_path(path: str) -> str:
    """
    Validate a Git-reported repository-relative path.

    Git paths are treated as data, not scope patterns.
    """

    if not isinstance(path, str) or not path:
        raise ScopeSyntaxError("Changed path is invalid")

    if (
        "\x00" in path
        or "\\" in path
        or path.startswith("/")
        or _DRIVE_PREFIX.match(path)
    ):
        raise ScopeSyntaxError("Changed path cannot be safely classified")

    segments = path.split("/")

    if any(segment in ("", ".", "..") for segment in segments):
        raise ScopeSyntaxError("Changed path contains invalid segments")

    return path


def assess_workspace(
    changes: Sequence[GitFileStatus],
    intended_scope: Sequence[str],
) -> WorkspaceAssessment:
    """
    Assess path overlap conservatively.

    A syntactically unsupported scope or changed path
    produces UNKNOWN, never NON_OVERLAPPING.

    This is an advisory overlap assessment, not a
    filesystem security enforcement mechanism.
    """

    changed_paths: set[str] = set()
    invalid_changed_path = False

    for change in changes:
        for raw_path in (
            change.path,
            change.original_path,
        ):
            if raw_path is None:
                continue

            try:
                changed_paths.add(_normalize_changed_path(raw_path))
            except ScopeSyntaxError:
                invalid_changed_path = True
                changed_paths.add(raw_path)

    ordered_paths = tuple(sorted(changed_paths))

    state = WorkspaceState.DIRTY if changes else WorkspaceState.CLEAN

    if invalid_changed_path or not intended_scope:
        return WorkspaceAssessment(
            state=state,
            overlap=OverlapStatus.UNKNOWN,
            changed_paths=ordered_paths,
            overlapping_paths=(),
        )

    parsed_scopes: list[ScopeExpression] = []

    try:
        for expression in intended_scope:
            parsed_scopes.append(parse_scope(expression))
    except ScopeSyntaxError:
        return WorkspaceAssessment(
            state=state,
            overlap=OverlapStatus.UNKNOWN,
            changed_paths=ordered_paths,
            overlapping_paths=(),
        )

    overlapping = {
        path
        for path in changed_paths
        if any(scope.matches(path) for scope in parsed_scopes)
    }

    overlap = OverlapStatus.NONE
    if changes:
        overlap = (
            OverlapStatus.OVERLAPPING if overlapping else OverlapStatus.NON_OVERLAPPING
        )

    return WorkspaceAssessment(
        state=state,
        overlap=overlap,
        changed_paths=ordered_paths,
        overlapping_paths=tuple(sorted(overlapping)),
    )


class GitPreflight:
    """Coordinate read-only Git preflight and optional baseline reconciliation."""

    def __init__(
        self,
        repository: GitRepository,
        config: AEWConfig,
        *,
        github: GitHubClient | None = None,
    ) -> None:
        self._repository = repository
        self._config = config
        self._github = github

    def _inspect_pull_requests(
        self,
        remote: str,
        issue: str,
        proposed_branch: str | None,
        intended_scope: Sequence[str],
        findings: list[PreflightFinding],
    ) -> tuple[GitHubPullRequest, ...] | None:
        github = self._github
        if github is None:
            findings.append(
                PreflightFinding(
                    "PR_PREFLIGHT_NOT_PERFORMED",
                    FindingSeverity.WARNING,
                    "Active PRs and concurrent branch dependencies were not inspected.",
                )
            )
            return None

        try:
            repository = self._repository.github_remote_repository(remote)
            if (
                repository is None
                or repository.casefold() != github.repository.casefold()
            ):
                findings.append(
                    PreflightFinding(
                        "PR_REPOSITORY_UNVERIFIED",
                        FindingSeverity.WARNING,
                        "The configured remote does not match the GitHub client repository.",
                        (remote, github.repository),
                    )
                )
                return None
            pull_requests = github.open_pull_requests()
        except (GitError, GitHubError) as error:
            findings.append(
                PreflightFinding(
                    "PR_COORDINATION_UNAVAILABLE",
                    FindingSeverity.WARNING,
                    "Complete pull request coordination evidence could not be retrieved.",
                    (github.repository, type(error).__name__),
                )
            )
            return None

        same_repo_heads = {
            pr.head_branch
            for pr in pull_requests
            if pr.head_repository
            and pr.head_repository.casefold() == repository.casefold()
        }
        issue_url = f"https://github.com/{repository}/issues/{issue}".casefold()
        for pr in pull_requests:
            evidence = (pr.url, pr.head_commit)
            assessment = assess_workspace(
                tuple(
                    GitFileStatus(path=path, index_status="M", worktree_status=" ")
                    for path in pr.changed_files
                ),
                intended_scope,
            )
            if assessment.overlapping_paths:
                findings.append(
                    PreflightFinding(
                        "PR_PATH_OVERLAP",
                        FindingSeverity.WARNING,
                        "An active pull request touches paths in the intended scope.",
                        (*evidence, *assessment.overlapping_paths),
                    )
                )
            if assessment.overlap == OverlapStatus.UNKNOWN:
                findings.append(
                    PreflightFinding(
                        "PR_PATH_SCOPE_UNKNOWN",
                        FindingSeverity.WARNING,
                        "An active pull request's path overlap could not be classified.",
                        evidence,
                    )
                )
            if any(url.casefold() == issue_url for url in pr.closing_issue_urls):
                findings.append(
                    PreflightFinding(
                        "PR_LINKED_ISSUE",
                        FindingSeverity.WARNING,
                        "An active pull request is linked to the requested issue.",
                        evidence,
                    )
                )
            if pr.base_branch in same_repo_heads or pr.base_branch == proposed_branch:
                findings.append(
                    PreflightFinding(
                        "PR_POSSIBLE_BRANCH_DEPENDENCY",
                        FindingSeverity.WARNING,
                        "An active pull request targets a branch relevant to coordination.",
                        (*evidence, pr.base_branch),
                    )
                )
        if proposed_branch is not None and proposed_branch in same_repo_heads:
            findings.append(
                PreflightFinding(
                    "PR_BRANCH_COLLISION",
                    FindingSeverity.BLOCKING,
                    "The proposed branch is the head of an active pull request in the integration repository.",
                    tuple(
                        pr.url
                        for pr in pull_requests
                        if pr.head_branch == proposed_branch
                        and pr.head_repository
                        and pr.head_repository.casefold() == repository.casefold()
                    ),
                )
            )
        return pull_requests

    def _inspect_baseline(
        self,
        branch: str,
        remote: str,
        tracking: str | None,
        findings: list[PreflightFinding],
    ) -> IntegrationBaseline:
        local_commit = self._repository.local_branch_commit(branch)
        remote_ref = f"{remote}/{branch}"
        try:
            remote_commit = self._repository.remote_branch_commit(branch, remote=remote)
        except GitError:
            remote_commit = None
            reason = "The integration remote could not be inspected."
        else:
            reason = "The configured branch was not found on the integration remote."

        if remote_commit is None:
            findings.append(
                PreflightFinding(
                    "INTEGRATION_REMOTE_UNAVAILABLE",
                    FindingSeverity.WARNING,
                    reason,
                    (remote_ref,),
                )
            )
            return IntegrationBaseline(
                remote, branch, tracking, local_commit, None, None, None
            )

        observed_at = datetime.now(UTC)
        object_available = self._repository.has_commit(remote_commit)
        if not object_available:
            findings.append(
                PreflightFinding(
                    "INTEGRATION_OBJECT_UNAVAILABLE",
                    FindingSeverity.WARNING,
                    "The observed remote commit is unavailable locally.",
                    (remote_ref, remote_commit),
                )
            )
        if tracking is not None and tracking != remote_commit:
            findings.append(
                PreflightFinding(
                    "INTEGRATION_TRACKING_MISMATCH",
                    FindingSeverity.WARNING,
                    "The local tracking ref differs from the observed remote HEAD.",
                    (remote_ref, tracking, remote_commit),
                )
            )
        if local_commit is not None and local_commit != remote_commit:
            findings.append(
                PreflightFinding(
                    "INTEGRATION_LOCAL_DIVERGENCE",
                    FindingSeverity.BLOCKING,
                    "The local integration branch differs from the observed remote HEAD.",
                    (branch, local_commit, remote_commit),
                )
            )
        return IntegrationBaseline(
            remote,
            branch,
            tracking,
            local_commit,
            remote_commit,
            observed_at,
            object_available,
        )

    def inspect(
        self,
        *,
        task_type: str,
        issue: str,
        title: str,
        intended_scope: Sequence[str],
        remote: str = "origin",
        verify_remote: bool = False,
    ) -> LocalPreflightReport:
        """Inspect the workspace and optionally observe the remote integration HEAD."""

        snapshot = self._repository.snapshot()

        workspace = assess_workspace(
            snapshot.changes,
            intended_scope,
        )

        findings: list[PreflightFinding] = []
        conflicts = tuple(
            sorted(change.path for change in snapshot.changes if change.conflicted)
        )
        if conflicts:
            findings.append(
                PreflightFinding(
                    "WORKSPACE_UNMERGED_PATHS",
                    FindingSeverity.BLOCKING,
                    "Resolve unmerged workspace paths before proceeding.",
                    conflicts,
                )
            )

        if snapshot.head_commit is None:
            findings.append(
                PreflightFinding(
                    code="GIT_UNBORN_HEAD",
                    severity=FindingSeverity.BLOCKING,
                    message=("Repository has no HEAD commit."),
                )
            )

        if snapshot.detached:
            findings.append(
                PreflightFinding(
                    code="GIT_DETACHED_HEAD",
                    severity=FindingSeverity.WARNING,
                    message=("Repository is in detached HEAD state."),
                )
            )

        if workspace.overlap == OverlapStatus.OVERLAPPING:
            findings.append(
                PreflightFinding(
                    code="WORKSPACE_OVERLAP",
                    severity=FindingSeverity.WARNING,
                    message=("Existing changes overlap the intended task scope."),
                    evidence=workspace.overlapping_paths,
                )
            )

        elif workspace.overlap == OverlapStatus.UNKNOWN:
            findings.append(
                PreflightFinding(
                    code="WORKSPACE_SCOPE_UNKNOWN",
                    severity=FindingSeverity.WARNING,
                    message=("Workspace overlap could not be safely determined."),
                    evidence=workspace.changed_paths,
                )
            )

        elif workspace.overlap == OverlapStatus.NON_OVERLAPPING:
            findings.append(
                PreflightFinding(
                    code="WORKSPACE_NON_OVERLAPPING",
                    severity=FindingSeverity.INFO,
                    message=(
                        "No path overlap was detected "
                        "within the supported scope syntax."
                    ),
                    evidence=workspace.changed_paths,
                )
            )

        integration_branch = self._config.integration_branch

        integration_commit = self._repository.integration_branch_commit(
            integration_branch,
            remote=remote,
        )

        if integration_commit is None:
            findings.append(
                PreflightFinding(
                    code="INTEGRATION_BASELINE_UNAVAILABLE",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "No locally known remote-tracking "
                        "integration commit is available."
                    ),
                    evidence=(f"{remote}/{integration_branch}",),
                )
            )

        baseline = None
        if verify_remote:
            baseline = self._inspect_baseline(
                integration_branch, remote, integration_commit, findings
            )

        proposed_branch: str | None = None
        branch_collision: bool | None = None

        try:
            candidate = self._config.generate_branch_name(
                task_type=task_type,
                issue=issue,
                title=title,
            )

            if not self._repository.is_valid_branch_name(candidate):
                findings.append(
                    PreflightFinding(
                        code="INVALID_BRANCH_NAME",
                        severity=FindingSeverity.BLOCKING,
                        message=("Generated branch name is invalid according to Git."),
                        evidence=(candidate,),
                    )
                )
            else:
                proposed_branch = candidate

                branch_collision = self._repository.branch_exists(
                    candidate,
                    remote=remote,
                )

                if branch_collision:
                    findings.append(
                        PreflightFinding(
                            code="BRANCH_COLLISION",
                            severity=FindingSeverity.BLOCKING,
                            message=(
                                "The proposed branch already "
                                "exists in known references."
                            ),
                            evidence=(candidate,),
                        )
                    )

        except (ConfigurationError, ValueError) as error:
            findings.append(
                PreflightFinding(
                    code="BRANCH_GENERATION_FAILED",
                    severity=FindingSeverity.BLOCKING,
                    message=str(error),
                )
            )

        if not verify_remote:
            findings.append(
                PreflightFinding(
                    code="REMOTE_FRESHNESS_NOT_VERIFIED",
                    severity=FindingSeverity.WARNING,
                    message=(
                        "Remote freshness has not been verified by local preflight."
                    ),
                )
            )
        pull_requests = self._inspect_pull_requests(
            remote, issue, proposed_branch, intended_scope, findings
        )
        if any(finding.code == "PR_BRANCH_COLLISION" for finding in findings):
            branch_collision = True
        remote_branch_collision = None
        if (
            proposed_branch is not None
            and verify_remote
            and self._config.check_remote_collision
        ):
            remote_branch_collision = self._check_remote_branch(
                remote, proposed_branch, findings
            )
            if branch_collision is not True:
                branch_collision = remote_branch_collision
        elif proposed_branch is not None and (
            verify_remote or pull_requests is not None
        ):
            findings.append(
                PreflightFinding(
                    "REMOTE_BRANCH_COLLISION_NOT_VERIFIED",
                    FindingSeverity.WARNING,
                    "The proposed branch has not been checked against live remote refs.",
                    (remote, proposed_branch),
                )
            )

        baseline_verified = bool(
            baseline
            and baseline.object_available
            and baseline.remote_commit == baseline.tracking_commit
        )
        evidence_complete = (
            baseline_verified
            and remote_branch_collision is not None
            and proposed_branch is not None
            and workspace.overlap != OverlapStatus.UNKNOWN
            and pull_requests is not None
            and not any(finding.code == "PR_PATH_SCOPE_UNKNOWN" for finding in findings)
        )
        severities = {finding.severity for finding in findings}
        if FindingSeverity.BLOCKING in severities:
            status = PreflightStatus.BLOCKED
        elif not evidence_complete:
            status = PreflightStatus.UNAVAILABLE
        elif FindingSeverity.WARNING in severities:
            status = PreflightStatus.WARNING
        else:
            status = PreflightStatus.PASSED

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
            remote_freshness_verified=baseline_verified,
            baseline=baseline,
            pull_requests_checked=pull_requests is not None,
            pull_requests=pull_requests or (),
            remote_branch_collision=remote_branch_collision,
            intended_scope=tuple(intended_scope),
        )

    def _check_remote_branch(
        self, remote: str, branch: str, findings: list[PreflightFinding]
    ) -> bool | None:
        reference = f"{remote}/{branch}"
        try:
            commit = self._repository.remote_branch_commit(branch, remote=remote)
        except GitError:
            findings.append(
                PreflightFinding(
                    "REMOTE_BRANCH_COLLISION_UNAVAILABLE",
                    FindingSeverity.WARNING,
                    "The proposed branch could not be checked against live remote refs.",
                    (reference,),
                )
            )
            return None
        if commit is not None:
            findings.append(
                PreflightFinding(
                    "REMOTE_BRANCH_COLLISION",
                    FindingSeverity.BLOCKING,
                    "The proposed branch already exists on the configured remote.",
                    (reference, commit),
                )
            )
        return commit is not None
