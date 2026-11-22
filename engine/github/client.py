"""
AEW read-only GitHub adapter.

Version: 0.1.0

Provides:
- GitHub repository identification.
- Issue retrieval.
- Open pull request discovery.
- Pull request detail and changed-file retrieval.
- Remote branch HEAD inspection.
- Conservative path-overlap analysis.

Uses the GitHub CLI (gh).

All operations are read-only. The adapter does not
create, edit, close, merge, push, or approve anything.

Requirements:
    Python 3.11+
    GitHub CLI installed and authenticated

Security:
    - No shell interpolation.
    - Explicit command allowlisting.
    - Bounded execution time.
    - Bounded response size.
    - Explicit repository selection.
    - Fail closed on incomplete pagination.
    - No implicit authentication changes.

This is not an authorization or execution engine.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


class GitHubError(RuntimeError):
    """Base exception for GitHub adapter failures."""


class GitHubCommandError(GitHubError):
    """Raised when a GitHub CLI command fails."""


class GitHubDataError(GitHubError):
    """Raised when GitHub returns unexpected data."""


class GitHubUnavailableError(GitHubError):
    """Raised when GitHub cannot be inspected."""


_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

_COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{40,64}$")

_ALLOWED_COMMANDS = {
    ("issue", "view"),
    ("pr", "list"),
    ("pr", "view"),
    ("api",),
}


@dataclass(frozen=True)
class GitHubIssue:
    repository: str
    number: int
    title: str
    body: str
    state: str
    url: str
    labels: tuple[str, ...]
    assignees: tuple[str, ...]


@dataclass(frozen=True)
class GitHubPullRequest:
    repository: str
    number: int
    title: str
    body: str
    state: str
    url: str
    base_branch: str
    head_branch: str
    head_repository: str | None
    head_commit: str
    draft: bool
    changed_files: tuple[str, ...]


@dataclass(frozen=True)
class PullRequestOverlap:
    pull_request_number: int
    overlapping_paths: tuple[str, ...]
    possible_overlap: bool


def _require_repository(repository: str) -> str:
    """Validate an explicit owner/repository identifier."""

    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("Repository must use the form owner/name")

    owner, name = repository.split("/", 1)

    if owner in (".", "..") or name in (".", ".."):
        raise ValueError("Repository identifier contains invalid segments")

    if owner.endswith(".") or name.endswith("."):
        raise ValueError("Repository identifier contains invalid segments")

    return repository


def _require_positive_number(number: int) -> int:
    """Validate a GitHub issue or pull request number."""

    if type(number) is not int or number < 1:
        raise ValueError("GitHub issue/PR number must be positive")

    return number


def _require_string(
    data: dict[str, Any],
    key: str,
) -> str:
    value = data.get(key)

    if not isinstance(value, str):
        raise GitHubDataError(f"Expected string field: {key}")

    return value


def _response_number(data: dict[str, Any]) -> int:
    try:
        return _require_positive_number(data.get("number"))
    except ValueError as error:
        raise GitHubDataError("Expected positive integer field: number") from error


def _require_commit(commit: str) -> str:
    if not _COMMIT_PATTERN.fullmatch(commit):
        raise GitHubDataError(f"Invalid Git commit identifier: {commit}")

    return commit


def _string_names(
    values: Any,
    *,
    key: str,
) -> tuple[str, ...]:
    """Extract name/login fields from GitHub objects."""

    if not isinstance(values, list):
        raise GitHubDataError(f"Expected list field: {key}")

    names: list[str] = []

    for item in values:
        if not isinstance(item, dict):
            raise GitHubDataError(f"Invalid entry in {key}")

        field = "login" if key == "assignees" else "name"
        value = item.get(field)

        if not isinstance(value, str):
            raise GitHubDataError(f"Invalid {field} in {key}")

        names.append(value)

    return tuple(names)


def _parse_issue(
    repository: str,
    data: dict[str, Any],
) -> GitHubIssue:
    return GitHubIssue(
        repository=repository,
        number=_response_number(data),
        title=_require_string(data, "title"),
        body=_require_string(data, "body"),
        state=_require_string(data, "state"),
        url=_require_string(data, "url"),
        labels=_string_names(
            data.get("labels"),
            key="labels",
        ),
        assignees=_string_names(
            data.get("assignees"),
            key="assignees",
        ),
    )


def _parse_pull_request(
    repository: str,
    data: dict[str, Any],
) -> GitHubPullRequest:
    """Parse GitHub CLI pull request JSON."""

    files = data.get("files")

    if not isinstance(files, list):
        raise GitHubDataError("Pull request files are unavailable")

    paths: list[str] = []

    for file in files:
        if not isinstance(file, dict):
            raise GitHubDataError("Invalid pull request file entry")

        path = file.get("path")

        if not isinstance(path, str) or not path:
            raise GitHubDataError("Invalid pull request file path")

        paths.append(path)

    head_repository = data.get("headRepositoryOwner")

    head_owner: str | None = None

    if isinstance(head_repository, dict):
        login = head_repository.get("login")

        if isinstance(login, str):
            head_owner = login

    head_branch = _require_string(
        data,
        "headRefName",
    )

    return GitHubPullRequest(
        repository=repository,
        number=_response_number(data),
        title=_require_string(data, "title"),
        body=_require_string(data, "body"),
        state=_require_string(data, "state"),
        url=_require_string(data, "url"),
        base_branch=_require_string(
            data,
            "baseRefName",
        ),
        head_branch=head_branch,
        head_repository=(
            f"{head_owner}/{head_branch}" if head_owner is not None else None
        ),
        head_commit=_require_commit(_require_string(data, "headRefOid")),
        draft=data["isDraft"],
        changed_files=tuple(sorted(set(paths))),
    )


class GitHubClient:
    """Read-only GitHub CLI client."""

    def __init__(
        self,
        repository: str,
        *,
        executable: str = "gh",
        timeout_seconds: int = 20,
        max_response_bytes: int = 8_000_000,
    ) -> None:
        self.repository = _require_repository(repository)

        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")

        if max_response_bytes < 1024:
            raise ValueError("max_response_bytes must be >= 1024")

        self._executable = executable
        self._timeout = timeout_seconds
        self._max_response_bytes = max_response_bytes

    def _run_json(
        self,
        arguments: Sequence[str],
    ) -> Any:
        """Execute one explicitly allowed read-only command."""

        if not arguments:
            raise GitHubCommandError("Empty GitHub command")

        prefix = tuple(arguments[:2])

        allowed = prefix in _ALLOWED_COMMANDS or (
            arguments[0] == "api" and ("api",) in _ALLOWED_COMMANDS
        )

        if not allowed:
            raise GitHubCommandError("GitHub operation is not allowlisted")

        environment = os.environ.copy()

        environment["GH_PROMPT_DISABLED"] = "1"
        environment["GIT_TERMINAL_PROMPT"] = "0"
        environment["GH_PAGER"] = "cat"

        try:
            result = subprocess.run(
                [self._executable, *arguments],
                capture_output=True,
                timeout=self._timeout,
                env=environment,
                check=False,
            )
        except FileNotFoundError as error:
            raise GitHubUnavailableError(
                "GitHub CLI executable is unavailable"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise GitHubUnavailableError("GitHub CLI request timed out") from error
        except OSError as error:
            raise GitHubUnavailableError("Unable to execute GitHub CLI") from error

        if result.returncode != 0:
            raise GitHubCommandError(
                "GitHub CLI command failed: "
                + result.stderr.decode(
                    "utf-8",
                    errors="replace",
                ).strip()[:1000]
            )

        if len(result.stdout) > self._max_response_bytes:
            raise GitHubDataError("GitHub response exceeds configured limit")

        try:
            return json.loads(result.stdout.decode("utf-8"))
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise GitHubDataError("GitHub returned invalid JSON") from error

    def issue(self, number: int) -> GitHubIssue:
        """Retrieve one issue."""

        number = _require_positive_number(number)

        data = self._run_json(
            [
                "issue",
                "view",
                str(number),
                "--repo",
                self.repository,
                "--json",
                ("number,title,body,state,url,labels,assignees"),
            ]
        )

        if not isinstance(data, dict):
            raise GitHubDataError("Expected issue object")

        return _parse_issue(
            self.repository,
            data,
        )

    def open_pull_request_numbers(
        self,
        *,
        limit: int = 100,
    ) -> tuple[int, ...]:
        """
        Discover open PR numbers.

        Fail closed when the result reaches the limit,
        because completeness cannot be established.
        """

        if limit < 1 or limit > 1000:
            raise ValueError("PR limit must be between 1 and 1000")

        data = self._run_json(
            [
                "pr",
                "list",
                "--repo",
                self.repository,
                "--state",
                "open",
                "--limit",
                str(limit),
                "--json",
                "number",
            ]
        )

        if not isinstance(data, list):
            raise GitHubDataError("Expected pull request list")

        if len(data) >= limit:
            raise GitHubDataError("Pull request enumeration may be incomplete")

        numbers: list[int] = []

        for item in data:
            if not isinstance(item, dict):
                raise GitHubDataError("Invalid pull request list entry")

            numbers.append(_response_number(item))

        if len(numbers) != len(set(numbers)):
            raise GitHubDataError("Duplicate pull request numbers")

        return tuple(numbers)

    def pull_request(
        self,
        number: int,
    ) -> GitHubPullRequest:
        """Retrieve one PR and its changed-file paths."""

        number = _require_positive_number(number)

        data = self._run_json(
            [
                "pr",
                "view",
                str(number),
                "--repo",
                self.repository,
                "--json",
                (
                    "number,title,body,state,url,"
                    "baseRefName,headRefName,"
                    "headRefOid,headRepositoryOwner,"
                    "isDraft,files"
                ),
            ]
        )

        if not isinstance(data, dict):
            raise GitHubDataError("Expected pull request object")

        if not isinstance(
            data.get("isDraft"),
            bool,
        ):
            raise GitHubDataError("Expected boolean isDraft")

        return _parse_pull_request(
            self.repository,
            data,
        )

    def open_pull_requests(
        self,
        *,
        limit: int = 100,
    ) -> tuple[GitHubPullRequest, ...]:
        """Retrieve complete metadata for open PRs."""

        numbers = self.open_pull_request_numbers(limit=limit)

        return tuple(self.pull_request(number) for number in numbers)

    def remote_branch_commit(
        self,
        branch: str,
    ) -> str:
        """
        Retrieve remote branch HEAD from GitHub API.

        This does not update local remote-tracking refs.
        """

        if (
            not isinstance(branch, str)
            or not branch
            or branch.startswith("/")
            or ".." in branch
            or any(character in branch for character in ("\x00", "\n", "\r"))
        ):
            raise ValueError("Invalid remote branch name")

        owner, name = self.repository.split("/", 1)

        # GitHub's Git ref endpoint accepts a branch
        # name with slash-separated path components.
        endpoint = f"repos/{owner}/{name}/git/ref/heads/{branch}"

        data = self._run_json(
            [
                "api",
                "--method",
                "GET",
                endpoint,
            ]
        )

        if not isinstance(data, dict):
            raise GitHubDataError("Expected Git reference object")

        obj = data.get("object")

        if not isinstance(obj, dict):
            raise GitHubDataError("Missing Git reference object")

        return _require_commit(_require_string(obj, "sha"))


def assess_pr_overlap(
    pull_requests: Sequence[GitHubPullRequest],
    intended_paths: Sequence[str],
) -> tuple[PullRequestOverlap, ...]:
    """
    Compare exact paths with active PR changed files.

    This is advisory and deliberately conservative.

    Directory scopes and globs are not interpreted here.
    An empty intended scope cannot establish independence.
    """

    intended = set(intended_paths)
    results: list[PullRequestOverlap] = []

    for pull_request in pull_requests:
        overlapping = tuple(sorted(intended.intersection(pull_request.changed_files)))

        results.append(
            PullRequestOverlap(
                pull_request_number=pull_request.number,
                overlapping_paths=overlapping,
                possible_overlap=(not intended or bool(overlapping)),
            )
        )

    return tuple(results)
