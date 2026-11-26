"""Validate a Git-backed Markdown knowledge vault at an immutable revision."""

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from engine.git.repository import GitRepository

_ID = re.compile(r"kb:[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*")
_STATUSES = ("draft", "active", "needs_review", "deprecated", "superseded", "archived")
_KINDS = ("principle", "pattern", "practice", "reference", "decision", "lesson")
_VISIBILITIES = ("private", "team", "shared")
_REQUIRED = (
    "id",
    "title",
    "status",
    "kind",
    "visibility",
    "created",
    "updated",
    "sources",
)
_RELATIONS = ("related", "supersedes", "superseded_by")


class _FrontmatterLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):
            return super().construct_mapping(node, deep)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ConstructorError(problem="Expected unique string metadata keys")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


@dataclass(frozen=True)
class VaultDocument:
    id: str
    path: str
    blob: str
    title: str
    status: str
    kind: str
    visibility: str
    created: date
    updated: date
    sources: tuple[tuple[str, str], ...]
    relations: tuple[tuple[str, str], ...]
    applicability: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class Vault:
    commit: str
    documents: tuple[VaultDocument, ...]

    def find(
        self, query: str = "", *, identifier: str | None = None
    ) -> tuple[VaultDocument, ...]:
        """Return active, shared notes and links to other retrievable notes."""
        available = {
            note.id: note
            for note in self.documents
            if note.status == "active" and note.visibility == "shared"
        }
        if identifier is not None and identifier not in available:
            raise ValueError("No active shared note with that ID")
        candidates = (
            (available[identifier],) if identifier is not None else available.values()
        )
        terms = query.casefold().split()
        matches = []
        for note in candidates:
            searchable = " ".join(
                (note.id, note.title, note.kind, *note.applicability, note.body)
            ).casefold()
            if all(term in searchable for term in terms):
                relations = tuple(
                    link for link in note.relations if link[1] in available
                )
                matches.append(replace(note, relations=relations))
        return tuple(sorted(matches, key=lambda note: note.id))


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def _date(value: object, field: str) -> date:
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise ValueError(f"{field} must be a valid YYYY-MM-DD date")


def _list(value: object, field: str) -> list:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return value


def _document(path: str, blob: str, content: str) -> VaultDocument:
    lines = content.removeprefix("\ufeff").splitlines(keepends=True)
    if not lines or lines[0].rstrip() != "---":
        raise ValueError("Missing YAML frontmatter")
    end = next(
        (i for i, line in enumerate(lines[1:], 1) if line.rstrip() == "---"), None
    )
    if end is None:
        raise ValueError("Unterminated YAML frontmatter")
    try:
        metadata = yaml.load("".join(lines[1:end]), Loader=_FrontmatterLoader)
    except (yaml.YAMLError, ValueError, OverflowError, RecursionError) as error:
        raise ValueError("Invalid YAML frontmatter or duplicate keys") from error
    if not isinstance(metadata, dict):
        raise TypeError("Frontmatter must be a mapping")
    missing = [field for field in _REQUIRED if field not in metadata]
    if missing:
        raise ValueError(f"Missing metadata fields: {', '.join(missing)}")

    identifier = _text(metadata["id"], "id")
    if not _ID.fullmatch(identifier):
        raise ValueError("id must use the kb:<namespace>:<identifier> format")
    for field, choices in (
        ("status", _STATUSES),
        ("kind", _KINDS),
        ("visibility", _VISIBILITIES),
    ):
        if metadata[field] not in choices:
            raise ValueError(f"{field} must be one of {', '.join(choices)}")
    created = _date(metadata["created"], "created")
    updated = _date(metadata["updated"], "updated")
    if updated < created:
        raise ValueError("updated must be on or after created")
    sources = []
    for source in _list(metadata["sources"], "sources"):
        if not isinstance(source, dict):
            raise TypeError("Each source must have a type and value")
        sources.append(
            (
                _text(source.get("type"), "source type"),
                _text(source.get("value"), "source value"),
            )
        )
    if not sources:
        raise ValueError("sources must contain provenance")

    relations = []
    for relation in _RELATIONS:
        targets = metadata.get(relation, [])
        if relation == "superseded_by" and isinstance(targets, str):
            targets = [targets]
        for target in _list(targets, relation):
            if not _ID.fullmatch(_text(target, relation)) or target == identifier:
                raise ValueError(f"{relation} must reference another knowledge ID")
            relations.append((relation, target))
    applicability = metadata.get("applicability", [])
    if isinstance(applicability, str):
        applicability = [applicability]
    return VaultDocument(
        identifier,
        path,
        blob,
        _text(metadata["title"], "title"),
        metadata["status"],
        metadata["kind"],
        metadata["visibility"],
        created,
        updated,
        tuple(sources),
        tuple(relations),
        tuple(
            _text(item, "applicability")
            for item in _list(applicability, "applicability")
        ),
        "".join(lines[end + 1 :]),
    )


def load_vault(path: Path, commit: str | None = None) -> Vault:
    """Read managed Markdown under path using only regular Git blobs."""
    path = path.resolve()
    repository = GitRepository(path)
    region = path.relative_to(repository.root).as_posix()
    commit = commit if commit is not None else repository.head_commit()
    if not commit:
        raise ValueError("Vault requires a committed Git revision")
    documents: dict[str, VaultDocument] = {}
    for entry in repository.committed_files(commit, region):
        if not entry.path.lower().endswith(".md"):
            continue
        try:
            content = repository.read_blob(entry.oid, max_bytes=1024 * 1024)
            if content is None:
                raise ValueError("Markdown must be UTF-8 text of at most 1 MiB")
            document = _document(entry.path, entry.oid, content)
            if document.id in documents:
                raise ValueError(
                    f"Duplicate knowledge ID also in {documents[document.id].path}"
                )
        except (TypeError, ValueError) as error:
            raise ValueError(f"{entry.path}: {error}") from error
        documents[document.id] = document
    for document in documents.values():
        for relation, target in document.relations:
            if target not in documents:
                raise ValueError(
                    f"{document.path}: unresolved {relation} reference {target}"
                )
    if not documents:
        raise ValueError("No committed Markdown documents found in the vault")
    return Vault(commit, tuple(documents.values()))
