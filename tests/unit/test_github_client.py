import json
import subprocess
from unittest.mock import Mock

import pytest

from engine.github.client import (
    GitHubClient,
    GitHubCommandError,
    GitHubDataError,
    GitHubUnavailableError,
    assess_pr_overlap,
)


@pytest.fixture
def run_cli(monkeypatch: pytest.MonkeyPatch) -> Mock:
    run = Mock()
    monkeypatch.setattr("engine.github.client.subprocess.run", run)
    return run


def response(payload: object) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess([], 0, json.dumps(payload).encode(), b"")


@pytest.fixture
def pull_request_data() -> dict[str, object]:
    return {
        "number": 7,
        "title": "Improve search",
        "body": "",
        "state": "OPEN",
        "url": "https://github.com/example/api/pull/7",
        "baseRefName": "master",
        "baseRefOid": "b" * 40,
        "headRefName": "search",
        "headRefOid": "a" * 40,
        "isCrossRepository": False,
        "isDraft": False,
        "changedFiles": 2,
        "closingIssuesReferences": [
            {"url": "https://github.com/example/api/issues/14"}
        ],
    }


def test_issue_uses_explicit_repository_and_disables_prompts(run_cli: Mock) -> None:
    run_cli.return_value = response(
        {
            "number": 14,
            "title": "Improve search",
            "body": "",
            "state": "OPEN",
            "url": "https://github.com/example/api/issues/14",
            "labels": [{"name": "enhancement"}],
            "assignees": [{"login": "example-dev"}],
        }
    )

    issue = GitHubClient("example/api", timeout_seconds=5).issue(14)

    assert issue.repository == "example/api"
    assert issue.number == 14
    assert issue.labels == ("enhancement",)
    assert issue.assignees == ("example-dev",)
    args, kwargs = run_cli.call_args
    assert args[0][:6] == ["gh", "issue", "view", "14", "--repo", "example/api"]
    assert kwargs["timeout"] == 5
    assert kwargs["env"]["GH_PROMPT_DISABLED"] == "1"
    assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_open_pull_requests_load_changed_files(
    run_cli: Mock, pull_request_data: dict[str, object]
) -> None:
    run_cli.side_effect = [
        response([{"number": 7}]),
        response(pull_request_data),
        response(
            [
                [
                    {
                        "filename": "src/search.py",
                        "status": "renamed",
                        "previous_filename": "src/old.py",
                    }
                ],
                [{"filename": "README.md", "status": "modified"}],
            ]
        ),
        response(pull_request_data),
    ]

    pull_requests = GitHubClient("example/api").open_pull_requests()

    assert [pr.number for pr in pull_requests] == [7]
    assert pull_requests[0].changed_files == (
        "README.md",
        "src/old.py",
        "src/search.py",
    )
    assert pull_requests[0].head_repository == "example/api"
    assert pull_requests[0].closing_issue_urls == (
        "https://github.com/example/api/issues/14",
    )
    (overlap,) = assess_pr_overlap(pull_requests, ["src/search.py"])
    assert overlap.possible_overlap
    assert overlap.overlapping_paths == ("src/search.py",)
    (unknown,) = assess_pr_overlap(pull_requests, [])
    assert unknown.possible_overlap
    assert unknown.overlapping_paths == ()
    listing, detail, files, recheck = (call.args[0] for call in run_cli.call_args_list)
    assert listing[:9] == [
        "gh",
        "pr",
        "list",
        "--repo",
        "example/api",
        "--state",
        "open",
        "--limit",
        "100",
    ]
    assert detail[:6] == ["gh", "pr", "view", "7", "--repo", "example/api"]
    assert files == [
        "gh",
        "api",
        "--method",
        "GET",
        "--paginate",
        "--slurp",
        "repos/example/api/pulls/7/files?per_page=100",
    ]
    assert recheck[:6] == detail[:6]


@pytest.mark.parametrize(
    ("pages", "message"),
    [
        ([[{"filename": "README.md"}]], "enumeration may be incomplete"),
        ([[{"filename": "README.md"}]] * 2, "duplicate pull request file path"),
        ([[{"filename": "README.md", "status": "renamed"}]], "previous_filename"),
    ],
)
def test_incomplete_pull_request_files_fail_closed(
    run_cli: Mock, pull_request_data: dict[str, object], pages: object, message: str
) -> None:
    run_cli.side_effect = [response(pull_request_data), response(pages)]
    with pytest.raises(GitHubDataError, match=message):
        GitHubClient("example/api").pull_request(7)


def test_pull_request_head_change_invalidates_paths(
    run_cli: Mock, pull_request_data: dict[str, object]
) -> None:
    run_cli.side_effect = [
        response(pull_request_data),
        response([[{"filename": "README.md"}, {"filename": "src/search.py"}]]),
        response({**pull_request_data, "headRefOid": "c" * 40}),
    ]
    with pytest.raises(GitHubDataError, match="changed during file enumeration"):
        GitHubClient("example/api").pull_request(7)


@pytest.mark.parametrize(
    "arguments",
    [
        ["api", "--method", "POST", "repos/example/api/git/ref/heads/master"],
        ["api", "--method", "GET", "repos/other/api/git/ref/heads/master"],
        ["api", "--method", "GET", "repos/example/api/issues"],
    ],
)
def test_api_rejects_commands_outside_read_allowlist(
    run_cli: Mock, arguments: list[str]
) -> None:
    with pytest.raises(GitHubCommandError, match="not allowlisted"):
        GitHubClient("example/api")._run_json(arguments)
    run_cli.assert_not_called()


def test_open_pull_requests_at_limit_fail_closed(run_cli: Mock) -> None:
    run_cli.return_value = response([{"number": 7}])

    with pytest.raises(GitHubDataError, match="enumeration may be incomplete"):
        GitHubClient("example/api").open_pull_requests(limit=1)

    run_cli.assert_called_once()


def test_remote_branch_head_uses_get(run_cli: Mock) -> None:
    sha = "b" * 40
    run_cli.return_value = response({"object": {"sha": sha}})

    assert GitHubClient("example/api").remote_branch_commit("release/v1") == sha
    assert run_cli.call_args.args[0] == [
        "gh",
        "api",
        "--method",
        "GET",
        "repos/example/api/git/ref/heads/release/v1",
    ]


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (FileNotFoundError(), "executable is unavailable"),
        (subprocess.TimeoutExpired("gh", 5), "request timed out"),
    ],
)
def test_cli_unavailable(
    run_cli: Mock, failure: OSError | subprocess.TimeoutExpired, message: str
) -> None:
    run_cli.side_effect = failure

    with pytest.raises(GitHubUnavailableError, match=message):
        GitHubClient("example/api").issue(14)


def test_cli_command_failure(run_cli: Mock) -> None:
    run_cli.return_value = subprocess.CompletedProcess(
        [], 1, b"", b"authentication required"
    )

    with pytest.raises(GitHubCommandError, match="authentication required"):
        GitHubClient("example/api").issue(14)


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        (b"not json", "invalid JSON"),
        (b"x" * 1025, "response exceeds configured limit"),
    ],
)
def test_invalid_cli_output(run_cli: Mock, stdout: bytes, message: str) -> None:
    run_cli.return_value = subprocess.CompletedProcess([], 0, stdout, b"")

    with pytest.raises(GitHubDataError, match=message):
        GitHubClient("example/api", max_response_bytes=1024).issue(14)


@pytest.mark.parametrize("number", [None, True, 0, "7"])
def test_invalid_pull_request_list_number(run_cli: Mock, number: object) -> None:
    run_cli.return_value = response([{} if number is None else {"number": number}])

    with pytest.raises(GitHubDataError, match="positive integer field: number"):
        GitHubClient("example/api").open_pull_request_numbers()
