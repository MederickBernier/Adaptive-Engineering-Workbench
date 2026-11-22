"""
Unit tests for AEW configuration management.

Covers:
- Built-in configuration defaults.
- User and project configuration precedence.
- Recursive configuration merging.
- Branch name generation.
- Invalid configuration handling.
- Git publication defaults.

Run:
    python -m pytest tests/unit/test_config.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from engine.config import (
    AEWConfig,
    ConfigurationError,
    load_config,
)


def write_config(
    path: Path,
    data: dict[str, Any],
) -> None:
    """Write a configuration fixture."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


@pytest.fixture
def config_paths(
    tmp_path: Path,
) -> tuple[Path, Path]:
    """Provide isolated repository and user config paths."""

    repository = tmp_path / "repository"
    repository.mkdir()

    user_config = tmp_path / "user" / "config.json"

    return repository, user_config


def load_test_config(
    repository: Path,
    user_config: Path,
) -> AEWConfig:
    """Load configuration using isolated test paths."""

    return load_config(
        repository,
        user_config_path=user_config,
    )


def test_default_configuration(
    config_paths: tuple[Path, Path],
) -> None:
    """Built-in defaults apply without config files."""

    repository, user_config = config_paths

    config = load_test_config(
        repository,
        user_config,
    )

    assert config.integration_branch == "master"
    assert config.branch_prefix == "mb/"

    assert config.branch_pattern == ("{prefix}{type}/{issue}-{slug}")


def test_default_publication_is_disabled(
    config_paths: tuple[Path, Path],
) -> None:
    """Git publication must be disabled by default."""

    repository, user_config = config_paths

    config = load_test_config(
        repository,
        user_config,
    )

    delivery = config.values["delivery"]

    assert delivery["commits"]["stage"] is False
    assert delivery["commits"]["execute"] is False

    assert delivery["push"]["execute"] is False

    assert delivery["pull_requests"]["create"] is False
    assert delivery["pull_requests"]["merge"] is False


def test_user_configuration_overrides_defaults(
    config_paths: tuple[Path, Path],
) -> None:
    """User configuration overrides built-in defaults."""

    repository, user_config = config_paths

    write_config(
        user_config,
        {"git": {"branches": {"prefix": "dev/"}}},
    )

    config = load_test_config(
        repository,
        user_config,
    )

    assert config.branch_prefix == "dev/"
    assert config.integration_branch == "master"


def test_project_configuration_overrides_user(
    config_paths: tuple[Path, Path],
) -> None:
    """Project configuration has higher precedence."""

    repository, user_config = config_paths

    write_config(
        user_config,
        {"git": {"branches": {"prefix": "personal/"}}},
    )

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"prefix": "team/"}}},
    )

    config = load_test_config(
        repository,
        user_config,
    )

    assert config.branch_prefix == "team/"


def test_nested_configuration_merge(
    config_paths: tuple[Path, Path],
) -> None:
    """Partial overrides preserve unrelated defaults."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"prefix": "mb/"}}},
    )

    config = load_test_config(
        repository,
        user_config,
    )

    branches = config.values["git"]["branches"]

    assert branches["prefix"] == "mb/"
    assert branches["check_remote_collision"] is True
    assert branches["create_from_integration"] is True


@pytest.mark.parametrize(
    ("task_type", "issue", "title", "expected"),
    [
        (
            "bug",
            "142",
            "Null Customer Response",
            "mb/fix/142-null-customer-response",
        ),
        (
            "feature",
            "187",
            "Add Rate Limiting",
            "mb/feat/187-add-rate-limiting",
        ),
        (
            "refactor",
            "215",
            "Authentication Service",
            "mb/refactor/215-authentication-service",
        ),
        (
            "documentation",
            "203",
            "Update API Documentation",
            "mb/docs/203-update-api-documentation",
        ),
    ],
)
def test_branch_name_generation(
    config_paths: tuple[Path, Path],
    task_type: str,
    issue: str,
    title: str,
    expected: str,
) -> None:
    """Generate predictable task branch names."""

    repository, user_config = config_paths

    config = load_test_config(
        repository,
        user_config,
    )

    branch = config.generate_branch_name(
        task_type=task_type,
        issue=issue,
        title=title,
    )

    assert branch == expected


def test_custom_branch_pattern(
    config_paths: tuple[Path, Path],
) -> None:
    """Branch naming patterns can be customized."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"naming_pattern": ("{prefix}{issue}-{slug}")}}},
    )

    config = load_test_config(
        repository,
        user_config,
    )

    assert (
        config.generate_branch_name(
            task_type="bug",
            issue="142",
            title="Null Customer Response",
        )
        == "mb/142-null-customer-response"
    )


def test_empty_branch_prefix(
    config_paths: tuple[Path, Path],
) -> None:
    """Projects may disable branch namespaces."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"prefix": ""}}},
    )

    config = load_test_config(
        repository,
        user_config,
    )

    assert (
        config.generate_branch_name(
            task_type="bug",
            issue="142",
            title="Null Customer Response",
        )
        == "fix/142-null-customer-response"
    )


@pytest.mark.parametrize(
    "prefix",
    [
        "/invalid/",
        "bad prefix/",
        "../",
        "bad//prefix/",
        "bad@{prefix}/",
    ],
)
def test_invalid_branch_prefix(
    config_paths: tuple[Path, Path],
    prefix: str,
) -> None:
    """Reject invalid branch namespace prefixes."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"prefix": prefix}}},
    )

    with pytest.raises(ConfigurationError):
        load_test_config(
            repository,
            user_config,
        )


def test_unknown_branch_token(
    config_paths: tuple[Path, Path],
) -> None:
    """Reject unsupported branch naming tokens."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"naming_pattern": ("{prefix}{unknown}/{slug}")}}},
    )

    with pytest.raises(
        ConfigurationError,
        match="Unknown branch naming tokens",
    ):
        load_test_config(
            repository,
            user_config,
        )


def test_missing_slug_token(
    config_paths: tuple[Path, Path],
) -> None:
    """Require a slug in branch naming patterns."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"git": {"branches": {"naming_pattern": ("{prefix}{type}/{issue}")}}},
    )

    with pytest.raises(
        ConfigurationError,
        match="must contain",
    ):
        load_test_config(
            repository,
            user_config,
        )


def test_invalid_boolean_configuration(
    config_paths: tuple[Path, Path],
) -> None:
    """Reject strings used instead of booleans."""

    repository, user_config = config_paths

    write_config(
        repository / ".aew" / "config.json",
        {"delivery": {"commits": {"execute": "false"}}},
    )

    with pytest.raises(
        ConfigurationError,
        match="must be a boolean",
    ):
        load_test_config(
            repository,
            user_config,
        )


def test_malformed_json(
    config_paths: tuple[Path, Path],
) -> None:
    """Malformed JSON must fail explicitly."""

    repository, user_config = config_paths

    path = repository / ".aew" / "config.json"

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        '{"git": ',
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError,
        match="Unable to load configuration",
    ):
        load_test_config(
            repository,
            user_config,
        )


def test_configuration_root_must_be_object(
    config_paths: tuple[Path, Path],
) -> None:
    """Reject JSON arrays as configuration roots."""

    repository, user_config = config_paths

    path = repository / ".aew" / "config.json"

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        '["invalid"]',
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError,
        match="root must be an object",
    ):
        load_test_config(
            repository,
            user_config,
        )


def test_empty_issue_identifier(
    config_paths: tuple[Path, Path],
) -> None:
    """Branch generation requires a valid task identifier."""

    repository, user_config = config_paths

    config = load_test_config(
        repository,
        user_config,
    )

    with pytest.raises(
        ConfigurationError,
        match="Issue identifier cannot be empty",
    ):
        config.generate_branch_name(
            task_type="bug",
            issue="",
            title="Null Customer Response",
        )


def test_empty_branch_slug(
    config_paths: tuple[Path, Path],
) -> None:
    """Reject titles that cannot produce a slug."""

    repository, user_config = config_paths

    config = load_test_config(
        repository,
        user_config,
    )

    with pytest.raises(
        ConfigurationError,
        match="Cannot generate branch slug",
    ):
        config.generate_branch_name(
            task_type="bug",
            issue="142",
            title="!!!",
        )


def test_branch_name_length_limit(
    config_paths: tuple[Path, Path],
) -> None:
    """Generated branches must respect the configured limit."""

    repository, user_config = config_paths

    config = load_test_config(
        repository,
        user_config,
    )

    with pytest.raises(
        ConfigurationError,
        match="exceeds 100 characters",
    ):
        config.generate_branch_name(
            task_type="feature",
            issue="187",
            title="Very Long Feature Name " * 20,
        )
