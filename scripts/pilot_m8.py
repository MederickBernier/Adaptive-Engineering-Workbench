"""Measure AEW intake and knowledge reuse on disposable pilot repositories."""

import argparse
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from engine.brain.discovery import discover
from engine.brain.retrieval import retrieve
from engine.brain.store import ProjectBrain
from engine.config import load_config
from engine.git.preflight import GitPreflight
from engine.git.repository import GitRepository
from engine.planning.assessment import Level, assess
from engine.planning.plan import Task
from engine.workflow.intake import Intake, plan_task

PILOTS = {
    "python-service": {
        "src/service.py": "def health():\n    return 'ok'\n",
        "pyproject.toml": '[project]\nname = "pilot"\ndependencies = ["fastapi"]\n[tool.pytest.ini_options]\n',
    },
    "java-application": {
        "src/Main.java": "public class Main { public static void main(String[] args) {} }\n",
        "pom.xml": "<project><modelVersion>4.0.0</modelVersion></project>\n",
    },
    "go-service": {
        "src/main.go": "package main\nfunc main() {}\n",
        "go.mod": "module example/pilot\n\ngo 1.22\n",
    },
    "mixed-application": {
        "backend/service.py": "def health():\n    return 'ok'\n",
        "frontend/index.ts": "export const status = 'ok';\n",
        "frontend/package.json": '{"dependencies":{"react":"18.3.1"}}\n',
    },
}


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=AEW Pilot",
            "-c",
            "user.email=pilot@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        timeout=20,
    )


def _fixture(root: Path, files: dict[str, str]) -> None:
    root.mkdir()
    _git(root, "init", "-b", "master")
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode())
    _git(root, "add", "--", *files)
    _git(root, "commit", "-m", "Record representative pilot sources")


def _measure(timings: dict[str, float], label: str, call):
    started = perf_counter()
    result = call()
    timings[label] = round((perf_counter() - started) * 1000, 1)
    return result


def _pilot(root: Path, database: Path, *, update_fixture: bool) -> dict:
    repository = GitRepository(root)
    before = repository.snapshot()
    brain = ProjectBrain(database, repository.root.as_uri())
    timings: dict[str, float] = {}
    config = load_config(repository.root)
    preflight = _measure(
        timings,
        "local_preflight_ms",
        lambda: GitPreflight(repository, config).inspect(
            task_type="task",
            issue="pilot",
            title="Inspect repository knowledge",
            intended_scope=("README.MD",),
        ),
    )
    initial = _measure(
        timings, "cold_discovery_ms", lambda: discover(repository, brain)
    )
    reopened = ProjectBrain(database, brain.repository)
    warm = _measure(
        timings, "warm_discovery_ms", lambda: discover(repository, reopened)
    )
    if warm != initial:
        raise RuntimeError("Repeated discovery did not reproduce the initial snapshot")
    view = _measure(
        timings, "retrieval_ms", lambda: retrieve(repository, reopened, initial.id)
    )
    intake = _measure(
        timings,
        "explore_intake_ms",
        lambda: plan_task(
            repository,
            reopened,
            Intake(
                Task(
                    "pilot",
                    brain.repository,
                    "Inspect engineering entry points",
                    ("Record source evidence",),
                ),
                assess(
                    risk=Level.LOW,
                    uncertainty=Level.HIGH,
                    rationale="Read-only pilot investigation",
                ),
                approach="Inspect committed discovery evidence",
                task_type="task",
                region=".",
                scope=("README.MD",),
                verification=("Record available project observations",),
                questions=("Which technologies are evidenced by the checkout?",),
                investigation_budget=4,
            ),
        ),
    )
    if repository.snapshot() != before or intake.state != "awaiting_approval":
        raise RuntimeError("Pilot intake crossed its advisory boundary")
    result = {
        "timings": timings,
        "preflight": preflight.status.value,
        "available_claims": len(view.current),
        "languages": sorted(
            {item.target for item in view.current if item.relation == "language"}
        ),
        "reused_snapshot": warm.id == initial.id,
        "checkout_unchanged_after_intake": True,
        "approval_requests": len(
            intake.revision.to_record()["task_document"]["approval"]["required_actions"]
        ),
    }
    if update_fixture:
        (root / "new-pilot-note.md").write_bytes(b"Committed pilot update\n")
        _git(root, "add", "--", "new-pilot-note.md")
        _git(root, "commit", "-m", "Advance pilot revision")
        updated = _measure(
            timings, "new_revision_discovery_ms", lambda: discover(repository, reopened)
        )
        if (
            updated.revision.commit == initial.revision.commit
            or reopened.load(initial.id) != initial
        ):
            raise RuntimeError("Pilot update failed to retain historical knowledge")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        help="Also inspect a real attached checkout read-only",
    )
    args = parser.parse_args()
    results = {}
    with TemporaryDirectory(prefix="aew-m8-") as temp:
        base = Path(temp)
        for label, files in PILOTS.items():
            root = base / label
            _fixture(root, files)
            results[label] = _pilot(
                root, base / f"{label}.sqlite3", update_fixture=True
            )
        if args.repository:
            results["real-checkout"] = _pilot(
                args.repository, base / "real.sqlite3", update_fixture=False
            )
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
