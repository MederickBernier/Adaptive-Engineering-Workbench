"""Evidence-backed discovery from a pinned, committed Git tree."""

import json
import re
import tomllib
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Any

from engine.brain.model import (
    Assertion,
    Depth,
    Evidence,
    Revision,
    Snapshot,
    Verification,
    validate_path,
)
from engine.brain.store import ProjectBrain
from engine.git.repository import GitRepository, GitTreeFile

_DETECTOR_VERSION = 1

_LANGUAGES = {
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}
_SIGNALS = {
    "pyproject.toml": ("manifest", "Python project metadata"),
    "package.json": ("manifest", "Node.js package metadata"),
    "requirements.txt": ("dependency_file", "Python requirements"),
    "poetry.lock": ("package_manager", "Poetry"),
    "uv.lock": ("package_manager", "uv"),
    "package-lock.json": ("package_manager", "npm"),
    "yarn.lock": ("package_manager", "Yarn"),
    "pnpm-lock.yaml": ("package_manager", "pnpm"),
    "go.mod": ("build_system", "Go modules"),
    "Cargo.toml": ("build_system", "Cargo"),
    "pom.xml": ("build_system", "Maven"),
    "build.gradle": ("build_system", "Gradle"),
    "build.gradle.kts": ("build_system", "Gradle"),
    "Makefile": ("build_system", "Make"),
    "pytest.ini": ("test_tool", "pytest"),
    "jest.config.js": ("test_tool", "Jest"),
    "ruff.toml": ("quality_tool", "Ruff"),
    ".ruff.toml": ("quality_tool", "Ruff"),
    ".editorconfig": ("convention_file", "EditorConfig"),
}
_DEPENDENCY_SIGNALS = {
    "django": ("framework", "Django"),
    "fastapi": ("framework", "FastAPI"),
    "flask": ("framework", "Flask"),
    "react": ("framework", "React"),
    "next": ("framework", "Next.js"),
    "vue": ("framework", "Vue"),
    "express": ("framework", "Express"),
    "pytest": ("test_tool", "pytest"),
    "jest": ("test_tool", "Jest"),
    "vitest": ("test_tool", "Vitest"),
    "ruff": ("quality_tool", "Ruff"),
    "eslint": ("quality_tool", "ESLint"),
    "prettier": ("quality_tool", "Prettier"),
}


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _manifest_facts(name: str, content: str) -> Iterable[tuple[str, str]]:
    if name == "package.json":
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Expected a package object")
        dependencies = set(_mapping(data.get("dependencies"))) | set(
            _mapping(data.get("devDependencies"))
        )
    else:
        data = tomllib.loads(content)
        project = _mapping(data.get("project"))
        groups = [
            project.get("dependencies"),
            *_mapping(project.get("optional-dependencies")).values(),
        ]
        dependencies = {
            match[0].lower()
            for group in groups
            if isinstance(group, list)
            for entry in group
            if isinstance(entry, str)
            if (match := re.match(r"[\w.-]+", entry.strip()))
        }
        build = _mapping(data.get("build-system")).get("build-backend")
        if isinstance(build, str) and build in {
            "setuptools.build_meta",
            "hatchling.build",
            "flit_core.buildapi",
            "poetry.core.masonry.api",
        }:
            yield "build_system", build
        tools = _mapping(data.get("tool"))
        dependencies.update(tools.keys() & {"pytest", "ruff"})
        line_length = _mapping(tools.get("ruff")).get("line-length")
        if type(line_length) is int and 1 <= line_length <= 320:
            yield "format_convention", f"Ruff line length {line_length}"
    for dependency in sorted(dependencies & _DEPENDENCY_SIGNALS.keys()):
        yield _DEPENDENCY_SIGNALS[dependency]


def _file_facts(
    repository: GitRepository, file: GitTreeFile
) -> Iterable[tuple[str, str, Depth]]:
    path = PurePosixPath(file.path)
    if language := _LANGUAGES.get(path.suffix.lower()):
        yield "language", language, Depth.DISCOVERY
    if signal := _SIGNALS.get(path.name):
        yield *signal, Depth.DISCOVERY
    if file.path.startswith(".github/workflows/") and path.suffix in (".yml", ".yaml"):
        yield "continuous_integration", "GitHub Actions", Depth.DISCOVERY
    if path.name not in ("package.json", "pyproject.toml"):
        return
    content = repository.read_blob(file.oid, max_bytes=512 * 1024)
    if content is None:
        yield (
            "inspection_limit",
            "Manifest exceeded the text inspection boundary",
            Depth.DISCOVERY,
        )
        return
    try:
        for relation, target in _manifest_facts(path.name, content):
            yield relation, target, Depth.STRUCTURAL
    except ValueError:
        yield "inspection_limit", "Manifest could not be parsed", Depth.DISCOVERY


def discover(
    repository: GitRepository,
    brain: ProjectBrain,
    *,
    commit: str | None = None,
    regions: tuple[str, ...] = (".",),
) -> Snapshot:
    """Publish broad discovery or targeted structural observations of committed files."""
    identity = repository.root.as_uri()
    if brain.repository != identity:
        raise ValueError("Project Brain identity does not match the Git checkout")
    commit = repository.head_commit() if commit is None else commit
    if commit is None:
        raise ValueError("Project Brain discovery requires a committed revision")
    revision = Revision(identity, commit)
    if not regions:
        raise ValueError("Discovery requires at least one region")

    coverage = tuple(sorted(set(regions)))
    for region in coverage:
        if region != ".":
            validate_path(region)
    cached = brain.cached_discovery(revision, coverage, _DETECTOR_VERSION)
    if cached is not None and repository.has_commit(revision.commit):
        return cached

    members: list[Assertion] = []
    for region in coverage:
        facts: dict[tuple[str, str, Depth], list[Evidence]] = {}
        for file in repository.committed_files(revision.commit, region):
            evidence = Evidence(
                f"git:blob:{file.oid}", "Observed in the committed tree", file.path
            )
            for fact in _file_facts(repository, file):
                facts.setdefault(fact, []).append(evidence)
            if "/" in file.path:
                parent = file.path.rsplit("/", 1)[0]
                facts.setdefault(
                    ("contains_region", parent, Depth.DISCOVERY), []
                ).append(evidence)
        members.extend(
            Assertion(
                revision,
                region,
                relation,
                target,
                tuple(evidence),
                region,
                depth,
                verification=Verification.VERIFIED,
            )
            for (relation, target, depth), evidence in facts.items()
        )
    snapshot = brain.publish(revision, coverage, members)
    brain.remember_discovery(snapshot, _DETECTOR_VERSION)
    return snapshot
