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

from engine.brain.discovery import discover
from engine.brain.model import Assertion, Depth, Evidence, Revision
from engine.brain.retrieval import retrieve
from engine.brain.store import ProjectBrain
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


def test_project_brain_discovers_pinned_regions(
    repository: Path, tmp_path: Path
) -> None:
    committed = {
        "backend/app.py": "print('hello')",
        "backend/pyproject.toml": '[project]\ndependencies = ["fastapi", "pytest"]\n'
        "[tool.ruff]\nline-length = 100\n",
        "frontend/app.ts": "export const value = 1;",
        "frontend/package.json": '{"dependencies": {"react": "*"}}',
        "frontend/package-lock.json": "{}",
        ".github/workflows/ci.yml": "name: CI",
    }
    for path, content in committed.items():
        file = repository / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Add discovery inputs")
    manifest = repository / "backend/pyproject.toml"
    manifest.write_text('[project]\ndependencies = ["django"]\n', encoding="utf-8")

    adapter = GitRepository(repository)
    brain = ProjectBrain(tmp_path / "brain.sqlite3", adapter.root.as_uri())
    broad = discover(adapter, brain)
    backend = discover(
        adapter, brain, commit=broad.revision.commit, regions=("backend",)
    )

    facts = {(item.relation, item.target) for item in broad.assertions}
    assert {
        ("language", "Python"),
        ("language", "TypeScript"),
        ("framework", "FastAPI"),
        ("framework", "React"),
        ("package_manager", "npm"),
        ("test_tool", "pytest"),
        ("continuous_integration", "GitHub Actions"),
        ("format_convention", "Ruff line length 100"),
    } <= facts
    assert ("framework", "Django") not in facts
    assert backend.regions == ("backend",)
    assert all(
        evidence.path and evidence.path.startswith("backend/")
        for item in backend.assertions
        for evidence in item.evidence
    )
    assert any(item.depth == Depth.STRUCTURAL for item in backend.assertions)
    assert brain.load(broad.id) == broad


def test_brain_retrieval_invalidates_changed_regions_and_dependents(
    repository: Path, tmp_path: Path
) -> None:
    for region in ("api", "storage", "ui"):
        file = repository / region / "source.py"
        file.parent.mkdir()
        file.write_text(f"# {region}", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "Establish component evidence")
    adapter = GitRepository(repository)
    old_commit = git(repository, "rev-parse", "HEAD")
    revision = Revision(adapter.root.as_uri(), old_commit)
    path = tmp_path / "brain.sqlite3"
    brain = ProjectBrain(path, revision.repository)

    def assertion(region: str, relation: str, target: str, depth: Depth) -> Assertion:
        return Assertion(
            revision,
            region,
            relation,
            target,
            (
                Evidence(
                    f"git:{old_commit}:{region}/source.py",
                    "Inspected source",
                    f"{region}/source.py",
                ),
            ),
            region,
            depth,
        )

    dependency = assertion("api", "depends_on", "storage", Depth.STRUCTURAL)
    api = assertion("api", "handles", "requests", Depth.BEHAVIORAL)
    storage = assertion("storage", "maintains", "data", Depth.SEMANTIC)
    ui = assertion("ui", "renders", "pages", Depth.DISCOVERY)
    snapshot = brain.publish(
        revision, ("api", "storage", "ui"), (dependency, api, storage, ui)
    )
    git(repository, "mv", "storage/source.py", "storage/renamed.py")
    git(repository, "commit", "-m", "Rename storage evidence")
    new_commit = git(repository, "rev-parse", "HEAD")

    reopened = ProjectBrain(path, revision.repository)
    assert reopened.snapshot_ids(old_commit) == (snapshot.id,)
    view = retrieve(adapter, reopened, snapshot.id, target_commit=new_commit)
    assert view.revision.commit == new_commit
    assert view.changed_paths == ("storage/renamed.py", "storage/source.py")
    assert view.affected_regions == ("api", "storage")
    assert view.current == (ui,)
    assert set(view.stale) == {dependency, api, storage}
    assert storage.depth is Depth.SEMANTIC
    assert retrieve(adapter, reopened, snapshot.id).stale == ()
    assert retrieve(
        adapter, reopened, snapshot.id, target_commit=new_commit, region="ui"
    ).current == (ui,)
    assert reopened.load(snapshot.id) == snapshot


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


@pytest.mark.parametrize(
    ("url", "identity"),
    [
        ("https://github.com/example/api.git", "example/api"),
        ("git@github.com:example/api.git", "example/api"),
        ("ssh://git@github.com/example/api", "example/api"),
        ("https://github.com.example.org/example/api.git", None),
    ],
)
def test_github_remote_identity(
    repository: Path, url: str, identity: str | None
) -> None:
    git(repository, "remote", "add", "origin", url)
    assert GitRepository(repository).github_remote_repository("origin") == identity


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
    before = git(repository, "show-ref")
    commit = git(repository, "rev-parse", "master")
    assert adapter.remote_branch_commit("master") == commit
    assert adapter.local_branch_commit("master") == commit
    assert adapter.has_commit(commit)
    assert adapter.remote_branch_commit("missing") is None
    assert adapter.local_branch_commit("missing") is None
    assert not adapter.has_commit("f" * 40)
    with pytest.raises(GitCommandError, match="remote is not configured"):
        adapter.remote_branch_commit("master", remote="missing")
    assert git(repository, "show-ref") == before


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
