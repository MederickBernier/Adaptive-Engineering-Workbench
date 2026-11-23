"""
AEW read-only Git repository adapter.

Provides:
- Repository discovery and identity.
- Current branch and HEAD commit.
- Working-tree status.
- Integration branch inspection.
- Local and remote branch discovery.
- Git-native branch-name validation.
- Local/remote branch collision detection.

This module never modifies repository state.

Requirements:
    Python 3.11+
    Git executable available on PATH

Notes:
    Network fetch and GitHub PR inspection are handled
    by separate preflight components.

    A local Git inspection is not a complete ADR-005
    preflight.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a Git operation fails."""


class RepositoryNotFoundError(GitError):
    """Raised when the path is not inside a Git repository."""


class GitCommandError(GitError):
    """Raised when a Git command fails unexpectedly."""


class WorkspaceState(str, Enum):
    CLEAN = "clean"
    DIRTY = "dirty"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GitFileStatus:
    """One changed path in the working tree."""

    path: str
    index_status: str
    worktree_status: str
    original_path: str | None = None

    @property
    def untracked(self) -> bool:
        return self.index_status == "?" and self.worktree_status == "?"

    @property
    def conflicted(self) -> bool:
        return (
            "U" in self.index_status
            or "U" in self.worktree_status
            or (self.index_status == "A" and self.worktree_status == "A")
            or (self.index_status == "D" and self.worktree_status == "D")
        )


@dataclass(frozen=True)
class GitBranch:
    """Git branch reference."""

    name: str
    commit: str
    remote: bool = False


@dataclass(frozen=True)
class GitTreeFile:
    path: str
    oid: str


@dataclass(frozen=True)
class RepositorySnapshot:
    """Read-only observation of repository state."""

    root: Path
    git_directory: Path
    branch: str | None
    head_commit: str | None
    detached: bool
    workspace_state: WorkspaceState
    changes: tuple[GitFileStatus, ...]


class GitRepository:
    """Read-only interface to a local Git repository."""

    def __init__(
        self,
        path: Path,
        *,
        git_executable: str = "git",
        timeout_seconds: int = 15,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")

        self._git = git_executable
        self._timeout = timeout_seconds
        self._requested_path = path.resolve()

        root = self._run(
            ["rev-parse", "--show-toplevel"],
            cwd=self._requested_path,
            check=False,
        )

        if root.returncode != 0:
            raise RepositoryNotFoundError(
                f"Not inside a Git working tree: {self._requested_path}"
            )

        self.root = Path(root.stdout.strip()).resolve()

        git_dir = self._run(
            ["rev-parse", "--absolute-git-dir"],
            cwd=self.root,
        )

        self.git_directory = Path(git_dir.stdout.strip()).resolve()

    def _run(
        self,
        arguments: Sequence[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a bounded Git command."""

        command = [
            self._git,
            "--no-optional-locks",
            *arguments,
        ]

        environment = os.environ.copy()

        environment["GIT_OPTIONAL_LOCKS"] = "0"
        environment["GIT_TERMINAL_PROMPT"] = "0"
        environment["GIT_NO_REPLACE_OBJECTS"] = "1"
        environment["GIT_NO_LAZY_FETCH"] = "1"

        try:
            result = subprocess.run(
                command,
                cwd=cwd or self._requested_path,
                capture_output=True,
                timeout=self._timeout,
                env=environment,
                check=False,
            )
        except FileNotFoundError as error:
            raise GitCommandError(f"Git executable not found: {self._git}") from error
        except subprocess.TimeoutExpired as error:
            raise GitCommandError(f"Git command timed out: {arguments}") from error
        except OSError as error:
            raise GitCommandError(f"Unable to execute Git: {error}") from error

        # Git status emits raw path bytes, including embedded line endings.
        stdout = result.stdout.decode("utf-8", errors="surrogateescape")
        stderr = result.stderr.decode("utf-8", errors="replace")
        if check and result.returncode != 0:
            raise GitCommandError(
                f"Git command failed ({result.returncode}): "
                f"{' '.join(arguments)}\n"
                f"{stderr.strip()}"
            )

        return subprocess.CompletedProcess(
            result.args, result.returncode, stdout, stderr
        )

    def current_branch(self) -> str | None:
        """Return branch name, or None for detached HEAD."""

        result = self._run(
            ["symbolic-ref", "--quiet", "--short", "HEAD"],
            check=False,
        )

        if result.returncode == 1:
            return None

        if result.returncode != 0:
            raise GitCommandError("Unable to resolve current branch")

        return result.stdout.strip()

    def head_commit(self) -> str | None:
        """Return HEAD commit, or None for an unborn branch."""

        result = self._run(
            ["rev-parse", "--verify", "HEAD"],
            check=False,
        )

        if result.returncode != 0:
            return None

        commit = result.stdout.strip()

        if not re.fullmatch(
            r"[0-9a-fA-F]{40,64}",
            commit,
        ):
            raise GitCommandError(f"Unexpected Git object ID: {commit}")

        return commit

    def changed_files(self) -> tuple[GitFileStatus, ...]:
        """Read staged, unstaged, and untracked changes."""

        result = self._run(
            [
                "-c",
                "core.quotePath=false",
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ],
        )

        entries = result.stdout.split("\0")
        if entries.pop() != "":
            raise GitCommandError("Unterminated Git porcelain status entry")
        changes: list[GitFileStatus] = []

        index = 0

        while index < len(entries):
            entry = entries[index]
            index += 1

            if len(entry) < 4 or entry[2] != " ":
                raise GitCommandError("Unexpected Git porcelain status entry")

            index_status = entry[0]
            worktree_status = entry[1]
            path = entry[3:]

            original_path: str | None = None

            if index_status in ("R", "C") or worktree_status in ("R", "C"):
                if index >= len(entries) or not entries[index]:
                    raise GitCommandError("Missing rename/copy source path")

                original_path = entries[index]
                index += 1

            changes.append(
                GitFileStatus(
                    path=path,
                    index_status=index_status,
                    worktree_status=worktree_status,
                    original_path=original_path,
                )
            )

        return tuple(changes)

    def workspace_state(self) -> WorkspaceState:
        """Return whether Git reports local changes."""

        return WorkspaceState.DIRTY if self.changed_files() else WorkspaceState.CLEAN

    def snapshot(self) -> RepositorySnapshot:
        """Capture a read-only repository observation."""

        branch = self.current_branch()
        commit = self.head_commit()
        changes = self.changed_files()

        return RepositorySnapshot(
            root=self.root,
            git_directory=self.git_directory,
            branch=branch,
            head_commit=commit,
            detached=branch is None,
            workspace_state=(WorkspaceState.DIRTY if changes else WorkspaceState.CLEAN),
            changes=changes,
        )

    def local_branches(self) -> tuple[GitBranch, ...]:
        """List local branches and their commits."""

        result = self._run(
            [
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ],
        )

        branches: list[GitBranch] = []

        for line in result.stdout.splitlines():
            if not line:
                continue

            name, separator, commit = line.partition("\0")

            if not separator:
                raise GitCommandError("Invalid local branch record")

            branches.append(
                GitBranch(
                    name=name,
                    commit=commit,
                    remote=False,
                )
            )

        return tuple(branches)

    def remote_branches(
        self,
        remote: str = "origin",
    ) -> tuple[GitBranch, ...]:
        """List locally known remote-tracking branches."""

        result = self._run(
            [
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                f"refs/remotes/{remote}",
            ],
        )

        branches: list[GitBranch] = []

        for line in result.stdout.splitlines():
            if not line:
                continue

            name, separator, commit = line.partition("\0")

            if not separator:
                raise GitCommandError("Invalid remote branch record")

            branches.append(
                GitBranch(
                    name=name,
                    commit=commit,
                    remote=True,
                )
            )

        return tuple(branches)

    def branch_exists(
        self,
        name: str,
        *,
        remote: str = "origin",
    ) -> bool:
        """Check local and known remote-tracking references."""

        if not self.is_valid_branch_name(name):
            return False

        local = self._run(
            [
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/heads/{name}",
            ],
            check=False,
        )

        if local.returncode == 0:
            return True

        if local.returncode != 1:
            raise GitCommandError("Unable to inspect local branch reference")

        remote_result = self._run(
            [
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/remotes/{remote}/{name}",
            ],
            check=False,
        )

        if remote_result.returncode == 0:
            return True

        if remote_result.returncode != 1:
            raise GitCommandError("Unable to inspect remote-tracking reference")

        return False

    def is_valid_branch_name(self, name: str) -> bool:
        """Validate a branch name using Git's native rules."""

        if not name:
            return False

        result = self._run(
            [
                "check-ref-format",
                "--branch",
                name,
            ],
            check=False,
        )

        return result.returncode == 0

    def integration_branch_commit(
        self,
        branch: str,
        *,
        remote: str = "origin",
    ) -> str | None:
        """
        Resolve a locally known integration baseline.

        This does not fetch or establish remote freshness.
        """

        if not self.is_valid_branch_name(branch):
            raise GitError(f"Invalid integration branch: {branch}")

        reference = f"refs/remotes/{remote}/{branch}"

        result = self._run(
            [
                "rev-parse",
                "--verify",
                reference,
            ],
            check=False,
        )

        if result.returncode != 0:
            return None

        return result.stdout.strip()

    def local_branch_commit(self, branch: str) -> str | None:
        """Resolve the commit at an exact local branch ref."""
        if not self.is_valid_branch_name(branch):
            raise GitError(f"Invalid integration branch: {branch}")

        result = self._run(
            ["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            check=False,
        )
        if result.returncode == 1:
            return None
        commit = result.stdout.strip()
        if result.returncode != 0 or not re.fullmatch(
            r"[0-9a-f]{40}|[0-9a-f]{64}", commit
        ):
            raise GitCommandError("Unable to resolve local integration branch")
        return commit

    def github_remote_repository(self, remote: str) -> str | None:
        """Identify a configured github.com remote without contacting it."""
        result = self._run(["remote", "get-url", "--", remote], check=False)
        if result.returncode != 0:
            return None
        match = re.fullmatch(
            r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
            r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?",
            result.stdout.strip(),
            flags=re.IGNORECASE,
        )
        return match[1] if match else None

    def remote_branch_commit(
        self, branch: str, *, remote: str = "origin"
    ) -> str | None:
        """Observe an exact branch on a configured remote without fetching objects."""
        if not self.is_valid_branch_name(branch):
            raise GitError(f"Invalid integration branch: {branch}")

        configured = self._run(["remote"]).stdout.splitlines()
        if not remote or remote not in configured:
            raise GitCommandError("Integration remote is not configured")

        reference = f"refs/heads/{branch}"
        result = self._run(
            [
                "-c",
                "protocol.ext.allow=never",
                "ls-remote",
                "--quiet",
                "--exit-code",
                "--refs",
                "--",
                remote,
                reference,
            ],
            check=False,
        )
        if result.returncode == 2:
            return None
        if result.returncode != 0:
            raise GitCommandError("Unable to query the integration remote")

        commit, _, observed_ref = result.stdout.rstrip("\r\n").partition("\t")
        if observed_ref != reference or not re.fullmatch(
            r"[0-9a-f]{40}|[0-9a-f]{64}", commit
        ):
            raise GitCommandError("Unexpected remote integration reference response")
        return commit

    def has_commit(self, commit: str) -> bool:
        """Check whether the exact object is locally available as a commit."""
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
            raise GitError("Expected a full Git object ID")
        result = self._run(
            ["rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == commit

    def committed_files(
        self, commit: str, region: str = ".", *, regular_only: bool = False
    ) -> tuple[GitTreeFile, ...]:
        """List regular files in a commit, optionally under a literal region."""
        if not self.has_commit(commit):
            raise GitError("Commit is not available locally")
        arguments = [
            "--literal-pathspecs",
            "ls-tree",
            "-r",
            "--full-tree",
            "-z",
            commit,
            "--",
        ]
        if region != ".":
            arguments.append(region)
        output = self._run(arguments).stdout
        entries = output.split("\0")
        if entries.pop() != "":
            raise GitCommandError("Unterminated Git tree record")
        files = []
        for entry in entries:
            metadata, separator, path = entry.partition("\t")
            fields = metadata.split()
            if not separator or not path or len(fields) != 3:
                raise GitCommandError("Unexpected Git tree record")
            mode, kind, oid = fields
            if kind == "blob" and mode in ("100644", "100755"):
                files.append(GitTreeFile(path, oid))
            elif regular_only:
                raise GitError("The execution checkout requires regular tracked files")
        return tuple(files)

    def read_blob(self, oid: str, *, max_bytes: int) -> str | None:
        """Read a bounded UTF-8 Git blob. Return None for oversized or binary input."""
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid):
            raise GitError("Expected a full Git object ID")
        size = int(self._run(["cat-file", "-s", oid]).stdout.strip())
        if size > max_bytes:
            return None
        content = self._run(["cat-file", "blob", oid]).stdout
        try:
            content.encode("utf-8")
        except UnicodeEncodeError:
            return None
        return None if "\x00" in content else content

    def changed_paths_between(
        self, old_commit: str, new_commit: str
    ) -> tuple[str, ...]:
        """Compare committed trees without running diff helpers or fetching objects."""
        if not self.has_commit(old_commit) or not self.has_commit(new_commit):
            raise GitError("Both revisions must be available locally for comparison")
        output = self._run(
            [
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--no-renames",
                "--no-relative",
                "--ignore-submodules=none",
                "--name-only",
                "-z",
                old_commit,
                new_commit,
                "--",
            ]
        ).stdout
        paths = output.split("\0")
        if paths.pop() != "" or any(not path for path in paths):
            raise GitCommandError("Unexpected Git changed-path record")
        return tuple(sorted(set(paths)))
