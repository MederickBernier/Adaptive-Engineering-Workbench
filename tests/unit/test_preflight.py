"""
Unit tests for AEW local Git preflight.

Covers:
- Clean and dirty workspace assessment.
- Overlapping and non-overlapping changes.
- Renamed files and unsupported scope patterns.
- Branch naming and collision detection.
- Missing integration baseline.
- Detached and unborn HEAD.
- Incomplete preflight reporting.

Run:
    python -m pytest tests/unit/test_preflight.py -v
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from engine.config import DEFAULT_CONFIG, AEWConfig
from engine.git.preflight import (
    FindingSeverity,
    GitPreflight,
    OverlapStatus,
    PreflightStatus,
    assess_workspace,
)
from engine.git.repository import (
    GitCommandError,
    GitFileStatus,
    RepositorySnapshot,
    WorkspaceState,
)
from engine.github.client import GitHubClient, GitHubDataError, GitHubPullRequest

COMMIT = "a" * 40
INTEGRATION_COMMIT = "b" * 40


def change(
    path: str,
    *,
    index: str = " ",
    worktree: str = "M",
    original: str | None = None,
) -> GitFileStatus:
    """Create a Git status fixture."""

    return GitFileStatus(
        path=path,
        index_status=index,
        worktree_status=worktree,
        original_path=original,
    )


def config() -> AEWConfig:
    """Create a default test configuration."""

    import copy

    return AEWConfig(values=copy.deepcopy(DEFAULT_CONFIG))


@dataclass
class FakeGitRepository:
    """Minimal read-only Git adapter test double."""

    changes: tuple[GitFileStatus, ...] = ()
    branch: str | None = "master"
    head: str | None = COMMIT
    integration_commit: str | None = INTEGRATION_COMMIT
    collision: bool = False
    valid_branch: bool = True
    local_commit: str | None = INTEGRATION_COMMIT
    remote_commit: str | None = INTEGRATION_COMMIT
    remote_error: bool = False
    object_available: bool = True
    github_repository: str | None = "example/api"
    remote_task_commit: str | None = None
    remote_task_error: bool = False

    def snapshot(self) -> RepositorySnapshot:
        return RepositorySnapshot(
            root=Path("/example/repository"),
            git_directory=Path("/example/repository/.git"),
            branch=self.branch,
            head_commit=self.head,
            detached=self.branch is None,
            workspace_state=(
                WorkspaceState.DIRTY if self.changes else WorkspaceState.CLEAN
            ),
            changes=self.changes,
        )

    def integration_branch_commit(
        self,
        branch: str,
        *,
        remote: str = "origin",
    ) -> str | None:
        assert branch == "master"
        assert remote == "origin"
        return self.integration_commit

    def is_valid_branch_name(
        self,
        name: str,
    ) -> bool:
        return self.valid_branch

    def local_branch_commit(self, branch: str) -> str | None:
        assert branch == "master"
        return self.local_commit

    def remote_branch_commit(self, branch: str, *, remote: str) -> str | None:
        assert remote == "origin"
        if branch != "master":
            assert branch == "mb/fix/142-null-customer-response"
            if self.remote_task_error:
                raise GitCommandError("Task branch lookup unavailable")
            return self.remote_task_commit
        if self.remote_error:
            raise GitCommandError("Remote unavailable")
        return self.remote_commit

    def has_commit(self, commit: str) -> bool:
        assert commit == self.remote_commit
        return self.object_available

    def github_remote_repository(self, remote: str) -> str | None:
        assert remote == "origin"
        return self.github_repository

    def branch_exists(
        self,
        name: str,
        *,
        remote: str = "origin",
    ) -> bool:
        assert remote == "origin"
        return self.collision


def inspect(
    repository: FakeGitRepository,
    *,
    scope: list[str] | None = None,
    verify_remote: bool = False,
    github: GitHubClient | None = None,
    check_remote_collision: bool = True,
):
    """Run preflight with consistent test inputs."""

    settings = config()
    settings.values["git"]["branches"]["check_remote_collision"] = (
        check_remote_collision
    )
    preflight = GitPreflight(
        repository,  # type: ignore[arg-type]
        settings,
        github=github,
    )

    return preflight.inspect(
        task_type="bug",
        issue="142",
        title="Null customer response",
        intended_scope=(scope if scope is not None else ["src/customer/**"]),
        verify_remote=verify_remote,
    )


def finding_codes(report: Any) -> set[str]:
    """Collect finding identifiers."""

    return {finding.code for finding in report.findings}


def test_matching_remote_baseline_keeps_preflight_incomplete() -> None:
    report = inspect(FakeGitRepository(), verify_remote=True)

    assert report.baseline is not None
    assert (
        report.baseline.remote_commit
        == report.baseline.tracking_commit
        == INTEGRATION_COMMIT
    )
    assert report.baseline.local_commit == INTEGRATION_COMMIT
    assert report.baseline.observed_at is not None
    assert report.baseline.object_available is True
    assert report.remote_freshness_verified is True
    assert report.status == PreflightStatus.UNAVAILABLE
    assert "PR_PREFLIGHT_NOT_PERFORMED" in finding_codes(report)
    assert report.remote_branch_collision is False


def test_live_remote_branch_collision_blocks_preflight() -> None:
    report = inspect(FakeGitRepository(remote_task_commit=COMMIT), verify_remote=True)

    assert report.remote_branch_collision is True
    assert report.branch_collision is True
    assert report.status == PreflightStatus.BLOCKED
    finding = next(
        item for item in report.findings if item.code == "REMOTE_BRANCH_COLLISION"
    )
    assert finding.evidence == ("origin/mb/fix/142-null-customer-response", COMMIT)


@pytest.mark.parametrize("local_collision", [False, True])
def test_remote_branch_lookup_failure_preserves_known_collision(
    local_collision: bool,
) -> None:
    report = inspect(
        FakeGitRepository(collision=local_collision, remote_task_error=True),
        verify_remote=True,
    )

    assert report.remote_branch_collision is None
    assert report.branch_collision is (True if local_collision else None)
    assert "REMOTE_BRANCH_COLLISION_UNAVAILABLE" in finding_codes(report)


def test_disabled_remote_collision_check_does_not_report_clearance() -> None:
    report = inspect(
        FakeGitRepository(remote_task_commit=COMMIT),
        verify_remote=True,
        check_remote_collision=False,
    )

    assert report.remote_branch_collision is None
    assert report.status == PreflightStatus.UNAVAILABLE
    assert "REMOTE_BRANCH_COLLISION_NOT_VERIFIED" in finding_codes(report)


def test_pull_request_coordination_reports_overlap_issue_dependency_and_collision() -> (
    None
):
    github = Mock(spec=GitHubClient, repository="example/api")
    parent = GitHubPullRequest(
        repository="example/api",
        number=7,
        title="Null response handling",
        body="",
        state="OPEN",
        url="https://github.com/example/api/pull/7",
        base_branch="master",
        head_branch="mb/fix/142-null-customer-response",
        head_repository="example/api",
        head_commit=COMMIT,
        draft=False,
        changed_files=("src/customer/mapper.py",),
        closing_issue_urls=("https://github.com/example/api/issues/142",),
    )
    child = replace(
        parent,
        number=8,
        url="https://github.com/example/api/pull/8",
        base_branch=parent.head_branch,
        head_branch="follow-up",
        changed_files=("README.md",),
        closing_issue_urls=(),
    )
    github.open_pull_requests.return_value = (parent, child)

    report = inspect(FakeGitRepository(), github=github, verify_remote=True)

    assert report.pull_requests == (parent, child)
    assert report.pull_requests_checked
    assert report.branch_collision is True
    assert report.status == PreflightStatus.BLOCKED
    assert {
        "PR_PATH_OVERLAP",
        "PR_LINKED_ISSUE",
        "PR_POSSIBLE_BRANCH_DEPENDENCY",
        "PR_BRANCH_COLLISION",
    } <= finding_codes(report)


def test_pull_request_coordination_requires_matching_identity() -> None:
    github = Mock(spec=GitHubClient, repository="other/api")

    report = inspect(FakeGitRepository(), github=github)

    assert not report.pull_requests_checked
    assert "PR_REPOSITORY_UNVERIFIED" in finding_codes(report)
    github.open_pull_requests.assert_not_called()


def test_incomplete_pull_request_evidence_does_not_clear_preflight() -> None:
    github = Mock(spec=GitHubClient, repository="example/api")
    github.open_pull_requests.side_effect = GitHubDataError("file count mismatch")

    report = inspect(FakeGitRepository(), github=github, verify_remote=True)

    assert report.remote_freshness_verified
    assert not report.pull_requests_checked
    assert report.status == PreflightStatus.UNAVAILABLE
    assert "PR_COORDINATION_UNAVAILABLE" in finding_codes(report)


def test_remote_baseline_reports_mismatches_and_missing_object() -> None:
    report = inspect(
        FakeGitRepository(remote_commit="c" * 40, object_available=False),
        verify_remote=True,
    )

    assert report.baseline is not None
    assert report.baseline.remote_commit == "c" * 40
    assert report.baseline.object_available is False
    assert report.remote_freshness_verified is False
    assert {
        "INTEGRATION_TRACKING_MISMATCH",
        "INTEGRATION_LOCAL_DIVERGENCE",
        "INTEGRATION_OBJECT_UNAVAILABLE",
    } <= finding_codes(report)


@pytest.mark.parametrize("remote_error", [True, False])
def test_unavailable_remote_preserves_local_observations(remote_error: bool) -> None:
    report = inspect(
        FakeGitRepository(remote_error=remote_error, remote_commit=None),
        verify_remote=True,
    )

    assert report.baseline is not None
    assert report.baseline.tracking_commit == INTEGRATION_COMMIT
    assert report.baseline.remote_commit is None
    assert report.baseline.observed_at is None
    assert report.remote_freshness_verified is False
    assert "INTEGRATION_REMOTE_UNAVAILABLE" in finding_codes(report)


def test_clean_workspace() -> None:
    """A clean workspace has no path overlap."""

    assessment = assess_workspace(
        [],
        ["src/customer/**"],
    )

    assert assessment.state == WorkspaceState.CLEAN
    assert assessment.overlap == OverlapStatus.NONE
    assert assessment.changed_paths == ()
    assert assessment.overlapping_paths == ()


def test_non_overlapping_workspace() -> None:
    """Unrelated changes should not block local work."""

    assessment = assess_workspace(
        [change("frontend/styles.css")],
        ["src/customer/**"],
    )

    assert assessment.state == WorkspaceState.DIRTY

    assert assessment.overlap == OverlapStatus.NON_OVERLAPPING

    assert assessment.changed_paths == ("frontend/styles.css",)

    assert assessment.overlapping_paths == ()


def test_overlapping_workspace() -> None:
    """Changes inside the task scope must be identified."""

    assessment = assess_workspace(
        [
            change("src/customer/CustomerMapper.java"),
            change("frontend/styles.css"),
        ],
        ["src/customer/**"],
    )

    assert assessment.overlap == OverlapStatus.OVERLAPPING

    assert assessment.overlapping_paths == ("src/customer/CustomerMapper.java",)


def test_exact_file_scope() -> None:
    """Exact file scopes should match precisely."""

    assessment = assess_workspace(
        [change("src/customer/CustomerMapper.java")],
        ["src/customer/CustomerMapper.java"],
    )

    assert assessment.overlap == OverlapStatus.OVERLAPPING


def test_directory_scope() -> None:
    """Directory scope includes descendant files."""

    assessment = assess_workspace(
        [change("src/customer/internal/Mapper.java")],
        ["src/customer/"],
    )

    assert assessment.overlap == OverlapStatus.OVERLAPPING


def test_unknown_scope() -> None:
    """Dirty workspace without scope remains unknown."""

    assessment = assess_workspace(
        [change("src/customer/CustomerMapper.java")],
        [],
    )

    assert assessment.overlap == OverlapStatus.UNKNOWN


@pytest.mark.parametrize(
    "scope",
    [
        "src/**/*.java",
        "src/*/CustomerMapper.java",
        "src/customer/?.java",
    ],
)
def test_unsupported_scope_patterns(
    scope: str,
) -> None:
    """Unsupported glob patterns must not imply safety."""

    assessment = assess_workspace(
        [change("src/customer/CustomerMapper.java")],
        [scope],
    )

    assert assessment.overlap == OverlapStatus.UNKNOWN


def test_rename_destination_overlap() -> None:
    """A rename into scope counts as overlapping."""

    assessment = assess_workspace(
        [
            change(
                "src/customer/NewMapper.java",
                index="R",
                worktree=" ",
                original="legacy/OldMapper.java",
            )
        ],
        ["src/customer/**"],
    )

    assert assessment.overlap == OverlapStatus.OVERLAPPING


def test_rename_source_overlap() -> None:
    """A rename out of scope still affects the source."""

    assessment = assess_workspace(
        [
            change(
                "frontend/NewMapper.java",
                index="R",
                worktree=" ",
                original="src/customer/OldMapper.java",
            )
        ],
        ["src/customer/**"],
    )

    assert assessment.overlap == OverlapStatus.OVERLAPPING


def test_local_preflight_is_incomplete() -> None:
    """Local checks alone cannot establish full preflight."""

    report = inspect(FakeGitRepository())

    assert report.status == PreflightStatus.UNAVAILABLE

    assert report.remote_freshness_verified is False
    assert report.pull_requests_checked is False

    assert "REMOTE_FRESHNESS_NOT_VERIFIED" in finding_codes(report)

    assert "PR_PREFLIGHT_NOT_PERFORMED" in finding_codes(report)


def test_proposed_branch_name() -> None:
    """Preflight uses configured naming conventions."""

    report = inspect(FakeGitRepository())

    assert report.proposed_branch == ("mb/fix/142-null-customer-response")

    assert report.branch_collision is False


def test_existing_branch_collision() -> None:
    """Existing task branches must be reported."""

    report = inspect(FakeGitRepository(collision=True))

    assert report.status == PreflightStatus.BLOCKED
    assert report.branch_collision is True

    assert "BRANCH_COLLISION" in finding_codes(report)


def test_invalid_generated_branch() -> None:
    """Git-invalid branch names block branch creation."""

    report = inspect(FakeGitRepository(valid_branch=False))

    assert report.status == PreflightStatus.BLOCKED
    assert report.proposed_branch is None

    assert "INVALID_BRANCH_NAME" in finding_codes(report)


def test_missing_integration_baseline() -> None:
    """Missing remote-tracking integration refs are reported."""

    report = inspect(FakeGitRepository(integration_commit=None))

    assert report.integration_commit is None

    assert "INTEGRATION_BASELINE_UNAVAILABLE" in finding_codes(report)

    assert report.status == PreflightStatus.UNAVAILABLE


def test_unborn_head() -> None:
    """Repositories without commits cannot proceed."""

    report = inspect(FakeGitRepository(head=None))

    assert report.status == PreflightStatus.BLOCKED
    assert "GIT_UNBORN_HEAD" in finding_codes(report)


def test_detached_head() -> None:
    """Detached HEAD must be explicitly reported."""

    report = inspect(FakeGitRepository(branch=None))

    assert "GIT_DETACHED_HEAD" in finding_codes(report)

    assert report.branch is None


def test_overlapping_changes_reported() -> None:
    """Overlapping paths appear in preflight evidence."""

    report = inspect(
        FakeGitRepository(changes=(change("src/customer/CustomerMapper.java"),))
    )

    assert "WORKSPACE_OVERLAP" in finding_codes(report)

    finding = next(item for item in report.findings if item.code == "WORKSPACE_OVERLAP")

    assert finding.severity == FindingSeverity.WARNING

    assert finding.evidence == ("src/customer/CustomerMapper.java",)


def test_non_overlapping_changes_reported() -> None:
    """Unrelated workspace edits are informational."""

    report = inspect(FakeGitRepository(changes=(change("frontend/styles.css"),)))

    assert "WORKSPACE_NON_OVERLAPPING" in finding_codes(report)

    assert report.status == PreflightStatus.UNAVAILABLE


def test_unknown_workspace_overlap_reported() -> None:
    """Unknown scope must be reported explicitly."""

    report = inspect(
        FakeGitRepository(changes=(change("src/customer/CustomerMapper.java"),)),
        scope=[],
    )

    assert "WORKSPACE_SCOPE_UNKNOWN" in finding_codes(report)

    assert report.workspace.overlap == OverlapStatus.UNKNOWN


def test_no_local_preflight_can_claim_passed() -> None:
    """Local-only preflight must never claim full success."""

    scenarios = [
        FakeGitRepository(),
        FakeGitRepository(changes=(change("frontend/styles.css"),)),
        FakeGitRepository(integration_commit=None),
        FakeGitRepository(collision=True),
        FakeGitRepository(branch=None),
    ]

    for repository in scenarios:
        report = inspect(repository)

        assert report.status != PreflightStatus.PASSED
