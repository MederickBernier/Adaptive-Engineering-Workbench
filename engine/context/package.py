"""Immutable, content-addressed Context Packages for the v0.1 contract."""

import json
from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from typing import Any

from engine.brain.model import validate_commit


class ContextPackageError(ValueError):
    """The package cannot be encoded or its integrity cannot be established."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for name, value in pairs:
        if name in result:
            raise ContextPackageError(f"Duplicate JSON property: {name}")
        result[name] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContextPackageError(f"Nonfinite JSON number: {value}")


def _decode(data: str | bytes) -> dict[str, Any]:
    try:
        value = json.loads(
            data.decode("utf-8") if isinstance(data, bytes) else data,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ContextPackageError("Expected a UTF-8 JSON package") from error
    if not isinstance(value, dict):
        raise ContextPackageError("Expected a JSON package object")
    return value


def _check_object_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContextPackageError("JSON object keys must be strings")
            _check_object_keys(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _check_object_keys(item)


def _encode(value: dict[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ContextPackageError("Package content must be finite JSON") from error


def _package_id(content: dict[str, Any]) -> str:
    return "ctx-sha256-" + sha256(_encode(content)).hexdigest()


def _require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContextPackageError(f"Package requires a nonempty {field}")


def _validate_binding(content: dict[str, Any]) -> None:
    if content.get("schema_version") != "0.1":
        raise ContextPackageError("Unsupported Context Package schema version")
    identity = content.get("identity")
    if not isinstance(identity, dict) or not isinstance(identity.get("revision"), dict):
        raise ContextPackageError("Package requires repository and revision binding")
    for field in ("task_id", "repository"):
        _require_text(identity.get(field), field)
    revision = identity["revision"]
    for field in ("branch", "commit", "snapshot_id"):
        _require_text(revision.get(field), field)
    try:
        validate_commit(revision["commit"].lower())
    except ValueError as error:
        raise ContextPackageError("Package requires a full Git commit") from error
    if not isinstance(content.get("integrity"), dict):
        raise ContextPackageError("Package requires an integrity section")
    if content.get("parent_package_id") is not None:
        _require_text(content["parent_package_id"], "parent_package_id")


@dataclass(frozen=True)
class ContextPackage:
    """A verified canonical JSON value that can be retained independently of storage."""

    _canonical_json: bytes

    def __post_init__(self) -> None:
        if not isinstance(self._canonical_json, bytes):
            raise ContextPackageError(
                "Canonical package content must be immutable bytes"
            )
        content = _decode(self._canonical_json)
        package_id = content.pop("package_id", None)
        _validate_binding(content)
        expected = _package_id(content)
        if (
            not isinstance(package_id, str)
            or not package_id.isascii()
            or not compare_digest(package_id, expected)
        ):
            raise ContextPackageError(
                "Context Package digest does not match its content"
            )
        if self._canonical_json != _encode({**content, "package_id": package_id}):
            raise ContextPackageError("Context Package bytes are not canonical")

    @classmethod
    def create(cls, content: dict[str, Any]) -> "ContextPackage":
        """Seal the supplied document and compute its Context Package identifier."""
        if "package_id" in content:
            raise ContextPackageError(
                "Package identity is assigned when sealing the content"
            )
        _check_object_keys(content)
        return cls(_encode({**content, "package_id": _package_id(content)}))

    @classmethod
    def from_json(cls, data: str | bytes) -> "ContextPackage":
        """Load a serialized document and reject a missing or mismatched digest."""
        return cls(_encode(_decode(data)))

    @property
    def package_id(self) -> str:
        return self.to_dict()["package_id"]

    def to_dict(self) -> dict[str, Any]:
        """Return a detached copy of the package document."""
        return _decode(self._canonical_json)

    def to_json(self) -> bytes:
        return self._canonical_json
