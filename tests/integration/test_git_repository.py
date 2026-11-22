"""
Integration tests for AEW's read-only Git adapter.

Tests use isolated temporary Git repositories.

Run:
    python -m pytest tests/integration/test_git_repository.py -v

Requirements:
    Python 3.11+
    pytest
    Git executable available on PATH

The adapter must not modify Git or workspace state.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from engine.git.repository import (
    GitCommandError,
    GitRepository,
    RepositoryNotFoundError,
    WorkspaceState,
)


def git(
    repository: Path,
    *arguments: str,
) -> str:
    """Execute Git inside a disposable test repository."""

    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=15,
    )

    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Create an isolated repository with one commit."""

    if shutil.which("git") is None:
        pytest.skip("Git executable is unavailable")

    root = tmp_path / "repository"
    root.mkdir()

    git(root, "init", "-b", "master")

    git(root, "config", "user.name", "AEW Test")
    git(root, "config", "user.email", "aew@example.invalid")

    (root / "README.md").write_text(
        "# Test Repository\n",
        encoding="utf-8",
    )

    git(root, "add", "README.md")
    git(root, "commit", "-m", "Initial commit")

    return root


def test_repository_discovery(
    repository: Path,
) -> None:
    """Discover the repository from a nested directory."""

    nested = repository / "src" / "customer"
    nested.mkdir(parents=True)

    adapter = GitRepository(nested)

    assert adapter.root == repository.resolve()
    assert adapter.git_directory.exists()


def test_non_repository_is_rejected(
    tmp_path: Path,
) -> None:
    """Reject paths outside a Git repository."""

    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(RepositoryNotFoundError):
        GitRepository(outside)


def test_clean_repository(
    repository: Path,
) -> None:
    """A committed repository starts clean."""

    adapter = GitRepository(repository)
    snapshot = adapter.snapshot()

    assert snapshot.branch == "master"
    assert snapshot.detached is False
    assert snapshot.workspace_state == WorkspaceState.CLEAN
    assert snapshot.changes == ()

    assert snapshot.head_commit == git(
        repository,
        "rev-parse",
        "HEAD",
    )


def test_unstaged_modification(
    repository: Path,
) -> None:
    """Detect modifications outside the Git index."""

    (repository / "README.md").write_text(
        "# Modified\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    change = changes[0]

    assert change.path == "README.md"
    assert change.index_status == " "
    assert change.worktree_status == "M"

    assert adapter.workspace_state() == WorkspaceState.DIRTY


def test_staged_modification(
    repository: Path,
) -> None:
    """Detect changes staged in the Git index."""

    (repository / "README.md").write_text(
        "# Staged\n",
        encoding="utf-8",
    )

    git(repository, "add", "README.md")

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    assert changes[0].index_status == "M"
    assert changes[0].worktree_status == " "


def test_untracked_file(
    repository: Path,
) -> None:
    """Detect untracked files."""

    (repository / "notes.txt").write_text(
        "Untracked content\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    assert changes[0].path == "notes.txt"
    assert changes[0].untracked is True


def test_multiple_changes(
    repository: Path,
) -> None:
    """Report staged, unstaged, and untracked changes."""

    (repository / "README.md").write_text(
        "# Modified\n",
        encoding="utf-8",
    )

    (repository / "new.txt").write_text(
        "New file\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)

    paths = {change.path for change in adapter.changed_files()}

    assert paths == {
        "README.md",
        "new.txt",
    }


def test_detached_head(
    repository: Path,
) -> None:
    """Recognize a detached HEAD without inventing a branch."""

    git(
        repository,
        "checkout",
        "--detach",
        "HEAD",
    )

    adapter = GitRepository(repository)
    snapshot = adapter.snapshot()

    assert snapshot.branch is None
    assert snapshot.detached is True
    assert snapshot.head_commit is not None


def test_local_branch_discovery(
    repository: Path,
) -> None:
    """List local branches and their commits."""

    git(
        repository,
        "branch",
        "mb/fix/142-null-response",
    )

    adapter = GitRepository(repository)

    branches = {branch.name: branch for branch in adapter.local_branches()}

    assert "master" in branches
    assert "mb/fix/142-null-response" in branches

    assert branches["master"].remote is False
    assert branches["master"].commit == git(
        repository,
        "rev-parse",
        "HEAD",
    )


@pytest.mark.parametrize(
    "branch_name",
    [
        "mb/fix/142-null-response",
        "feature/customer-api",
        "task/123",
        "release/v0.1.0",
    ],
)
def test_valid_branch_names(
    repository: Path,
    branch_name: str,
) -> None:
    """Accept valid Git branch references."""

    adapter = GitRepository(repository)

    assert adapter.is_valid_branch_name(branch_name) is True


@pytest.mark.parametrize(
    "branch_name",
    [
        "",
        "bad branch",
        "../invalid",
        "bad..branch",
        "bad@{branch}",
        "invalid.lock",
        "/absolute",
        "bad//branch",
    ],
)
def test_invalid_branch_names(
    repository: Path,
    branch_name: str,
) -> None:
    """Reject invalid Git branch references."""

    adapter = GitRepository(repository)

    assert adapter.is_valid_branch_name(branch_name) is False


def test_local_branch_collision(
    repository: Path,
) -> None:
    """Detect an existing local task branch."""

    name = "mb/fix/142-null-response"

    git(repository, "branch", name)

    adapter = GitRepository(repository)

    assert adapter.branch_exists(name) is True
    assert adapter.branch_exists("mb/fix/999-other") is False


def test_remote_tracking_branch(
    repository: Path,
    tmp_path: Path,
) -> None:
    """Inspect locally known remote-tracking references."""

    remote = tmp_path / "remote.git"
    remote.mkdir()

    git(remote, "init", "--bare")

    git(
        repository,
        "remote",
        "add",
        "origin",
        str(remote),
    )

    git(
        repository,
        "push",
        "-u",
        "origin",
        "master",
    )

    git(
        repository,
        "branch",
        "mb/fix/142-null-response",
    )

    git(
        repository,
        "push",
        "origin",
        "mb/fix/142-null-response",
    )

    adapter = GitRepository(repository)

    branches = adapter.remote_branches()

    names = {branch.name for branch in branches}

    assert "origin/master" in names
    assert "origin/mb/fix/142-null-response" in names

    assert adapter.integration_branch_commit("master") == git(
        repository,
        "rev-parse",
        "master",
    )


def test_renamed_file(
    repository: Path,
) -> None:
    """Parse a staged rename with its original path."""

    git(
        repository,
        "mv",
        "README.md",
        "DOCUMENTATION.md",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1

    change = changes[0]

    assert change.path == "DOCUMENTATION.md"
    assert change.original_path == "README.md"
    assert change.index_status == "R"


def test_unicode_filename(
    repository: Path,
) -> None:
    """Preserve Unicode filenames in Git status."""

    filename = "données-équipe.txt"

    (repository / filename).write_text(
        "Contenu de test\n",
        encoding="utf-8",
    )

    adapter = GitRepository(repository)
    changes = adapter.changed_files()

    assert len(changes) == 1
    assert changes[0].path == filename


@pytest.mark.parametrize("status", [b"R ", b"C "])
def test_status_preserves_raw_rename_and_copy_paths(
    repository: Path, monkeypatch: pytest.MonkeyPatch, status: bytes
) -> None:
    adapter = GitRepository(repository)
    output = status + b" destination\r\n.txt\0source-\xff.txt\0"

    def run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, output, b"")

    monkeypatch.setattr("engine.git.repository.subprocess.run", run)

    (change,) = adapter.changed_files()

    assert change.index_status == chr(status[0])
    assert change.path == "destination\r\n.txt"
    assert change.original_path == "source-\udcff.txt"


@pytest.mark.parametrize(
    ("output", "message"),
    [
        (b"?? file.txt", "Unterminated Git porcelain status entry"),
        (b"R  renamed.txt\0", "Missing rename/copy source path"),
        (b"C  copied.txt\0\0", "Missing rename/copy source path"),
        (b"\0?? file.txt\0", "Unexpected Git porcelain status entry"),
    ],
)
def test_status_rejects_incomplete_records(
    repository: Path, monkeypatch: pytest.MonkeyPatch, output: bytes, message: str
) -> None:
    adapter = GitRepository(repository)

    def run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, output, b"")

    monkeypatch.setattr("engine.git.repository.subprocess.run", run)

    with pytest.raises(GitCommandError, match=message):
        adapter.changed_files()


def test_adapter_does_not_modify_repository(
    repository: Path,
) -> None:
    """Read-only inspection must preserve Git state."""

    before_head = git(
        repository,
        "rev-parse",
        "HEAD",
    )

    before_status = git(
        repository,
        "status",
        "--porcelain",
    )

    adapter = GitRepository(repository)

    adapter.snapshot()
    adapter.local_branches()
    adapter.remote_branches()
    adapter.branch_exists("mb/fix/142")
    adapter.is_valid_branch_name("mb/fix/142")

    after_head = git(
        repository,
        "rev-parse",
        "HEAD",
    )

    after_status = git(
        repository,
        "status",
        "--porcelain",
    )

    assert before_head == after_head
    assert before_status == after_status


def test_missing_integration_branch(
    repository: Path,
) -> None:
    """Missing remote-tracking baseline returns None."""

    adapter = GitRepository(repository)

    assert adapter.integration_branch_commit("master") is None
