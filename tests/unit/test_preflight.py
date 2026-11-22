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

from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    GitFileStatus,
    RepositorySnapshot,
    WorkspaceState,
)

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
):
    """Run preflight with consistent test inputs."""

    preflight = GitPreflight(
        repository,  # type: ignore[arg-type]
        config(),
    )

    return preflight.inspect(
        task_type="bug",
        issue="142",
        title="Null customer response",
        intended_scope=(scope if scope is not None else ["src/customer/**"]),
    )


def finding_codes(report: Any) -> set[str]:
    """Collect finding identifiers."""

    return {finding.code for finding in report.findings}


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
