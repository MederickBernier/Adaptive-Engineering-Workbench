"""JSON task-planning interface. The trusted execution host is a separate caller."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from engine.brain.bootstrap import BootstrapInterview, scan_bootstrap
from engine.brain.store import ProjectBrain
from engine.config import (
    default_brain_path,
    describe_settings,
    load_config,
    resolve_vault_path,
)
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


def _brain_path(repository: GitRepository, override: Path | None) -> Path:
    path = (override or default_brain_path(repository.root)).resolve()
    if path.is_relative_to(repository.root):
        raise ValueError("Choose a Project Brain path outside the checkout")
    return path


def _config_show(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="aew-task config show",
        description="Show configuration without writing state or querying the network.",
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--brain", type=Path)
    parser.add_argument("--vault", type=Path)
    args = parser.parse_args(argv)
    try:
        repository = GitRepository(args.repository)
        config = load_config(repository.root)
        brain_path = _brain_path(repository, args.brain)
        vault_path, vault_source = resolve_vault_path(
            repository.root, config, args.vault
        )
        settings = describe_settings(config)
        branch = config.integration_branch
        source = settings["git.integration_branch"]["source"]
        if branch is None:
            branch = repository.remote_default_branch()
            source = "cached_remote_head" if branch else "unresolved"
        document = {
            "repository": repository.root.as_uri(),
            "files": [
                {"layer": layer, "path": str(path), "loaded": present}
                for layer, path, present in config.files
            ],
            "settings": settings,
            "project_brain": {
                "path": str(brain_path),
                "source": "command_line" if args.brain else "user_data_default",
            },
            "vault": {"path": str(vault_path), "source": vault_source},
            "integration_branch": {
                "value": branch,
                "source": source,
                "remote_verified": False,
            },
        }
    except (ValueError, GitError, OSError, RuntimeError) as error:
        print(
            json.dumps({"error": str(error), "state": "configuration_failed"}),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(document, sort_keys=True, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:2] == ["config", "show"]:
        return _config_show(argv[2:])
    if argv[:1] == ["bootstrap"]:
        return _bootstrap(argv[1:])
    if argv[:1] == ["vault"]:
        return _vault(argv[1:])
    parser = argparse.ArgumentParser(
        description="Prepare an advisory AEW task plan from JSON on stdin."
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--brain", type=Path)
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
        brain_path = _brain_path(repository, arguments.brain)
        request = _request(data, repository.root.as_uri())
        if arguments.brain is None:
            brain_path.parent.mkdir(parents=True, exist_ok=True)
        brain = ProjectBrain(brain_path, request.task.repository)
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


def _vault(argv: list[str]) -> int:
    from dataclasses import asdict

    from engine.brain.vault import load_vault

    parser = argparse.ArgumentParser(prog="aew-task vault")
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("validate", "search", "show"):
        command = commands.add_parser(action)
        command.add_argument(
            "--vault", type=Path, help="Override the configured vault path"
        )
        command.add_argument("--repository", type=Path, default=Path.cwd())
        command.add_argument("--commit", help="Full local commit ID (default: HEAD)")
        if action == "search":
            command.add_argument("--query", default="", help="Words to match in notes")
        if action == "show":
            command.add_argument("id", help="Stable knowledge ID")
    args = parser.parse_args(argv)
    try:
        path = args.vault
        if path is None:
            repository = GitRepository(args.repository)
            path, _ = resolve_vault_path(repository.root, load_config(repository.root))
        vault = load_vault(path.expanduser(), args.commit)
    except (GitError, OSError, ValueError, RuntimeError) as error:
        message = (
            str(error)
            if args.action == "validate"
            else "Unable to load vault. Run vault validate for details."
        )
        print(json.dumps({"error": message}), file=sys.stderr)
        return 1
    try:
        result: dict[str, Any] = {"commit": vault.commit}
        if args.action == "validate":
            result["documents"] = len(vault.documents)
        elif args.action == "search":
            result["documents"] = [
                {
                    "id": note.id,
                    "title": note.title,
                    "kind": note.kind,
                    "blob": note.blob,
                }
                for note in vault.find(args.query)
            ]
        else:
            note = vault.find(identifier=args.id)[0]
            result["document"] = {
                **asdict(note),
                "created": note.created.isoformat(),
                "updated": note.updated.isoformat(),
                "sources": [
                    {"type": kind, "value": value} for kind, value in note.sources
                ],
                "relations": [
                    {"type": kind, "target": target} for kind, target in note.relations
                ],
            }
    except ValueError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


def _bootstrap(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="aew-task bootstrap",
        description="Scan the committed repository and produce a draft review.",
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "action",
        nargs="?",
        choices=("scan", "start", "show", "answer", "publish"),
        default="scan",
    )
    parser.add_argument("--brain", type=Path)
    parser.add_argument("--session")
    parser.add_argument("--question")
    parser.add_argument("--expect", type=int)
    parser.add_argument("--maintainer")
    parser.add_argument(
        "--disposition", choices=("answered", "skipped", "deferred"), default="answered"
    )
    parser.add_argument("--answer")
    parser.add_argument("--review-digest")
    args = parser.parse_args(argv)
    try:
        repository = GitRepository(args.repository)
        if args.action == "scan":
            result = scan_bootstrap(repository)
        else:
            result = _bootstrap_interview(repository, args)
        print(json.dumps(result, sort_keys=True, indent=2))
    except (ValueError, GitError, OSError, sqlite3.Error) as error:
        print(
            json.dumps({"error": str(error), "state": "bootstrap_failed"}),
            file=sys.stderr,
        )
        return 1
    return 0


def _bootstrap_interview(
    repository: GitRepository, args: argparse.Namespace
) -> dict[str, Any]:
    path = _brain_path(repository, args.brain)
    if args.action == "start" and args.brain is None:
        path.parent.mkdir(parents=True, exist_ok=True)
    if args.action != "start" and (not args.session or not path.is_file()):
        raise ValueError("An existing database and --session are required")
    interview = BootstrapInterview(
        repository, ProjectBrain(path, repository.root.as_uri())
    )
    if args.action == "start":
        return interview.start()
    if args.action == "show":
        return interview.show(args.session)
    if args.action == "answer":
        if not args.question or args.expect is None or not args.maintainer:
            raise ValueError("Answer requires --question, --expect, and --maintainer")
        return interview.answer(
            args.session,
            expected_version=args.expect,
            question_id=args.question,
            maintainer=args.maintainer,
            disposition=args.disposition,
            answer=args.answer,
        )
    if not args.review_digest:
        raise ValueError(
            "Publish requires the --review-digest from the reviewed interview"
        )
    return interview.publish(args.session, review_digest=args.review_digest)


if __name__ == "__main__":
    raise SystemExit(main())
