"""Explicit first-time discovery and a draft interview for maintainers."""

from dataclasses import asdict
from typing import Any

from engine.brain.discovery import inspect_revision
from engine.brain.model import Revision
from engine.git.repository import GitRepository


def scan_bootstrap(repository: GitRepository) -> dict[str, Any]:
    commit = repository.head_commit()
    if commit is None:
        raise ValueError("Bootstrap requires a committed revision")
    revision = Revision(repository.root.as_uri(), commit)
    observations = inspect_revision(repository, revision, (".",))
    facts = {item.relation for item in observations}
    questions = [
        {
            "id": "ownership",
            "topic": "Components",
            "prompt": "Which components own the main business rules, and where are their boundaries?",
        },
        {
            "id": "dependencies",
            "topic": "Components",
            "prompt": "Which runtime dependencies or external integrations matter most to maintainers?",
        },
        {
            "id": "constraints",
            "topic": "Conventions",
            "prompt": "Which repository conventions, sensitive areas, or architectural decisions should future tasks respect?",
        },
    ]
    if "test_tool" not in facts:
        questions.append(
            {
                "id": "tests",
                "topic": "Verification",
                "prompt": "Which commands or checks are authoritative for verifying changes?",
            }
        )
    if "build_system" not in facts:
        questions.append(
            {
                "id": "build",
                "topic": "Verification",
                "prompt": "How do maintainers build or run this project?",
            }
        )
    return {
        "state": "draft",
        "revision": asdict(revision),
        "regions": ["."],
        "observations": [asdict(item) for item in observations],
        "questions": questions,
        "limitations": [
            "Committed regular files only. Observations cover recognized signals; questions require maintainer input."
        ],
    }
