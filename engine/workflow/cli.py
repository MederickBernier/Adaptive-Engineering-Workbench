"""JSON task-planning interface. The trusted execution host is a separate caller."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from engine.brain.store import ProjectBrain
from engine.git.repository import GitError, GitRepository
from engine.github.client import GitHubClient
from engine.planning.assessment import Level, Profile, assess
from engine.planning.plan import Task, WorkUnit
from engine.workflow.intake import Intake, plan_task


def _array(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("Expected an array of strings")
    return tuple(value)


def _request(data: dict[str, Any], repository: str) -> Intake:
    task = dict(data["task"])
    task["acceptance"] = _array(task.get("acceptance", []))
    if "constraints" in task:
        task["constraints"] = _array(task["constraints"])
    assessment = dict(data["assessment"])
    for field in ("risk", "uncertainty"):
        assessment[field] = Level(assessment[field])
    if "requested" in assessment:
        assessment["requested"] = Profile(assessment["requested"])
    if "evidence" in assessment:
        assessment["evidence"] = _array(assessment["evidence"])
    options = {
        key: value
        for key, value in data.items()
        if key not in ("task", "assessment", "work_units")
    }
    for key in ("scope", "verification", "questions", "assumptions"):
        if key in options:
            options[key] = _array(options[key])
    units = []
    for record in data.get("work_units", []):
        unit = dict(record)
        for key in ("scope", "verification", "acceptance", "dependencies"):
            if key in unit:
                unit[key] = _array(unit[key])
        units.append(WorkUnit(**unit))
    return Intake(
        Task(repository=repository, **task),
        assess(**assessment),
        work_units=tuple(units),
        **options,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare an advisory AEW task plan from JSON on stdin."
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--brain", type=Path, required=True)
    parser.add_argument("--verify-remote", action="store_true")
    parser.add_argument("--github-repository")
    arguments = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise ValueError("Intake JSON exceeds the byte limit")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise TypeError("Expected an intake JSON object")
        repository = GitRepository(arguments.repository)
        if arguments.brain.resolve().is_relative_to(repository.root):
            raise ValueError("Choose a Project Brain path outside the checkout")
        request = _request(data, repository.root.as_uri())
        brain = ProjectBrain(arguments.brain, request.task.repository)
        github = (
            GitHubClient(arguments.github_repository)
            if arguments.github_repository
            else None
        )
        result = plan_task(
            repository,
            brain,
            request,
            github=github,
            verify_remote=arguments.verify_remote,
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        GitError,
        sqlite3.Error,
        OSError,
    ) as error:
        print(
            json.dumps({"error": str(error), "state": "planning_failed"}),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "state": result.state,
                "context": result.context.to_dict(),
                "plan": result.revision.to_record(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
