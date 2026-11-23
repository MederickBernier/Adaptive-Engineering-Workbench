"""Immutable Project Brain values."""

import re
from dataclasses import dataclass
from enum import StrEnum


def validate_commit(commit: str) -> None:
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
        raise ValueError("Expected a full lowercase Git commit identifier")


def validate_path(path: str) -> None:
    if "\x00" in path or any(part in ("", ".", "..") for part in path.split("/")):
        raise ValueError("Expected a repository-relative Git path")


class Depth(StrEnum):
    DISCOVERY = "D0"
    STRUCTURAL = "D1"
    BEHAVIORAL = "D2"
    SEMANTIC = "D3"


class KnowledgeKind(StrEnum):
    DERIVED = "derived"
    DURABLE = "durable"


class Verification(StrEnum):
    VERIFIED = "verified"
    PROVISIONAL = "provisional"


@dataclass(frozen=True)
class Revision:
    repository: str
    commit: str
    branch: str | None = None

    def __post_init__(self) -> None:
        if not self.repository.strip():
            raise ValueError("Repository identity is required")
        validate_commit(self.commit)


@dataclass(frozen=True)
class Evidence:
    reference: str
    detail: str
    path: str | None = None

    def __post_init__(self) -> None:
        if not self.reference.strip() or not self.detail.strip():
            raise ValueError("Evidence reference and detail are required")
        if self.path is not None:
            validate_path(self.path)


@dataclass(frozen=True)
class Assertion:
    revision: Revision
    subject: str
    relation: str
    target: str
    evidence: tuple[Evidence, ...]
    region: str = "."
    depth: Depth = Depth.DISCOVERY
    kind: KnowledgeKind = KnowledgeKind.DERIVED
    verification: Verification = Verification.PROVISIONAL

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.subject, self.relation, self.target)
        ):
            raise ValueError("Assertion subject, relation and target are required")
        if not isinstance(self.evidence, tuple) or not self.evidence:
            raise ValueError("An assertion requires immutable evidence")
        if self.region != ".":
            validate_path(self.region)


@dataclass(frozen=True)
class Snapshot:
    id: str
    revision: Revision
    regions: tuple[str, ...]
    assertions: tuple[Assertion, ...]
    observed_at: str
