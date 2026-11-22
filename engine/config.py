
"""
AEW configuration management.

Configuration precedence:
    Built-in defaults
    < User configuration
    < Project configuration

Repository and organization policies are enforced
separately and cannot be overridden by these settings.

Configuration files use JSON in v0.1.0.

User configuration:
    ~/.config/aew/config.json

Project configuration:
    .aew/config.json
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class ConfigurationError(ValueError):
    """Raised when AEW configuration is invalid."""


DEFAULT_CONFIG: dict[str, Any] = {
    "git": {
        "integration_branch": "master",
        "branches": {
            "prefix": "mb/",
            "naming_pattern": "{prefix}{type}/{issue}-{slug}",
            "check_remote_collision": True,
            "create_from_integration": True,
        },
    },
    "tasks": {
        "planning": "adaptive",
        "default_work_units": "single",
    },
    "delivery": {
        "commits": {
            "strategy": "per_work_unit",
            "format": "conventional",
            "stage": False,
            "execute": False,
            "checkpoint": "sequential",
        },
        "pull_requests": {
            "create": False,
            "merge": False,
        },
        "push": {
            "execute": False,
        },
    },
}


BRANCH_TYPES: dict[str, str] = {
    "bug": "fix",
    "feature": "feat",
    "task": "task",
    "refactor": "refactor",
    "documentation": "docs",
}

ALLOWED_BRANCH_TOKENS = {
    "prefix",
    "type",
    "issue",
    "slug",
}

PREFIX_PATTERN = re.compile(
    r"^(?:[a-zA-Z0-9][a-zA-Z0-9._-]*/)*$"
)

SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON configuration file."""

    if not path.exists():
        return {}

    if not path.is_file():
        raise ConfigurationError(
            f"Configuration path is not a file: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            f"Unable to load configuration {path}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Configuration root must be an object: {path}"
        )

    return data


def _merge(
    base: dict[str, Any],
    override: Mapping[str, Any],
) -> dict[str, Any]:
    """Recursively merge configuration objects."""

    result = copy.deepcopy(base)

    for key, value in override.items():
        existing = result.get(key)

        if (
            isinstance(existing, dict)
            and isinstance(value, dict)
        ):
            result[key] = _merge(existing, value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def _require_bool(
    value: Any,
    field: str,
) -> bool:
    """Require an actual boolean, not a truthy value."""

    if not isinstance(value, bool):
        raise ConfigurationError(
            f"{field} must be a boolean"
        )

    return value


def _require_string(
    value: Any,
    field: str,
) -> str:
    """Require a nonempty string."""

    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(
            f"{field} must be a nonempty string"
        )

    return value


def _validate_branch_config(
    branches: Mapping[str, Any],
) -> None:
    """Validate branch naming configuration."""

    prefix = branches.get("prefix")
    pattern = branches.get("naming_pattern")

    if not isinstance(prefix, str):
        raise ConfigurationError(
            "git.branches.prefix must be a string"
        )

    if prefix and not PREFIX_PATTERN.fullmatch(prefix):
        raise ConfigurationError(
            "Invalid branch prefix. "
            "Expected a namespace such as 'mb/'."
        )

    pattern = _require_string(
        pattern,
        "git.branches.naming_pattern",
    )

    tokens = set(
        re.findall(r"\{([^{}]+)\}", pattern)
    )

    unknown = tokens - ALLOWED_BRANCH_TOKENS

    if unknown:
        raise ConfigurationError(
            "Unknown branch naming tokens: "
            + ", ".join(sorted(unknown))
        )

    if "{slug}" not in pattern:
        raise ConfigurationError(
            "Branch naming pattern must contain {slug}"
        )

    _require_bool(
        branches.get("check_remote_collision"),
        "git.branches.check_remote_collision",
    )

    _require_bool(
        branches.get("create_from_integration"),
        "git.branches.create_from_integration",
    )


def validate_config(
    config: Mapping[str, Any],
) -> None:
    """Validate the effective AEW configuration."""

    git = config.get("git")

    if not isinstance(git, dict):
        raise ConfigurationError(
            "git configuration must be an object"
        )

    _require_string(
        git.get("integration_branch"),
        "git.integration_branch",
    )

    branches = git.get("branches")

    if not isinstance(branches, dict):
        raise ConfigurationError(
            "git.branches must be an object"
        )

    _validate_branch_config(branches)

    delivery = config.get("delivery")

    if not isinstance(delivery, dict):
        raise ConfigurationError(
            "delivery configuration must be an object"
        )

    commits = delivery.get("commits")

    if not isinstance(commits, dict):
        raise ConfigurationError(
            "delivery.commits must be an object"
        )

    for field in ("stage", "execute"):
        _require_bool(
            commits.get(field),
            f"delivery.commits.{field}",
        )

    pull_requests = delivery.get("pull_requests")

    if not isinstance(pull_requests, dict):
        raise ConfigurationError(
            "delivery.pull_requests must be an object"
        )

    for field in ("create", "merge"):
        _require_bool(
            pull_requests.get(field),
            f"delivery.pull_requests.{field}",
        )

    push = delivery.get("push")

    if not isinstance(push, dict):
        raise ConfigurationError(
            "delivery.push must be an object"
        )

    _require_bool(
        push.get("execute"),
        "delivery.push.execute",
    )


@dataclass(frozen=True)
class AEWConfig:
    """Validated effective AEW configuration."""

    values: dict[str, Any]

    @property
    def integration_branch(self) -> str:
        return self.values["git"]["integration_branch"]

    @property
    def branch_prefix(self) -> str:
        return self.values["git"]["branches"]["prefix"]

    @property
    def branch_pattern(self) -> str:
        return self.values["git"]["branches"]["naming_pattern"]

    def generate_branch_name(
        self,
        *,
        task_type: str,
        issue: str,
        title: str,
    ) -> str:
        """Generate a proposed branch name."""

        branch_type = BRANCH_TYPES.get(
            task_type,
            task_type,
        )

        if not re.fullmatch(
            r"[a-zA-Z0-9_-]+",
            branch_type,
        ):
            raise ConfigurationError(
                f"Invalid branch type: {branch_type}"
            )

        issue_token = re.sub(
            r"[^a-zA-Z0-9_-]",
            "-",
            str(issue),
        ).strip("-")

        if not issue_token:
            raise ConfigurationError(
                "Issue identifier cannot be empty"
            )

        slug = SLUG_PATTERN.sub(
            "-",
            title.lower(),
        ).strip("-")

        if not slug:
            raise ConfigurationError(
                "Cannot generate branch slug from title"
            )

        values = {
            "prefix": self.branch_prefix,
            "type": branch_type,
            "issue": issue_token,
            "slug": slug,
        }

        try:
            branch = self.branch_pattern.format_map(values)
        except (KeyError, ValueError) as error:
            raise ConfigurationError(
                f"Invalid branch naming pattern: {error}"
            ) from error

        if len(branch) > 100:
            raise ConfigurationError(
                "Generated branch name exceeds 100 characters"
            )

        return branch


def load_config(
    repository_root: Path,
    *,
    user_config_path: Path | None = None,
) -> AEWConfig:
    """Load, merge, and validate AEW configuration."""

    if user_config_path is None:
        user_config_path = (
            Path.home()
            / ".config"
            / "aew"
            / "config.json"
        )

    project_config_path = (
        repository_root
        / ".aew"
        / "config.json"
    )

    config = copy.deepcopy(DEFAULT_CONFIG)

    config = _merge(
        config,
        _load_json(user_config_path),
    )

    config = _merge(
        config,
        _load_json(project_config_path),
    )

    validate_config(config)

    return AEWConfig(values=config)
