"""Reviewable changes prepared without writes to the shared checkout."""

import json
from dataclasses import asdict, dataclass
from difflib import unified_diff
from hashlib import sha256
from typing import TYPE_CHECKING

from engine.execution.authority import ExecutionDenied

if TYPE_CHECKING:
    from engine.context.package import ContextPackage
    from engine.execution.authority import SignedGrant
    from engine.execution.envelope import ExecutionEnvelope, ExecutionPolicy
    from engine.git.repository import GitRepository


_MAX_EDIT_BYTES = 512 * 1024
_MAX_DIFF_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class TextReplacement:
    path: str
    expected_oid: str | None
    content: str


@dataclass(frozen=True)
class ChangeReview:
    commit: str
    replacements: tuple[TextReplacement, ...]
    diff: str
    digest: str

    def verified_digest(self) -> str:
        binding = json.dumps(
            {
                "commit": self.commit,
                "replacements": [asdict(item) for item in self.replacements],
                "diff": self.diff,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        observed = sha256(binding).hexdigest()
        if observed != self.digest:
            raise ExecutionDenied("Review digest does not match its content")
        return observed


def prepare_changes(
    repository: "GitRepository",
    policy: "ExecutionPolicy",
    envelope: "ExecutionEnvelope",
    context: "ContextPackage",
    signed: "SignedGrant",
    replacements: tuple[TextReplacement, ...],
) -> ChangeReview:
    """Check exact committed file versions and produce a review-only diff."""
    if type(replacements) is not tuple or not 1 <= len(replacements) <= 256:
        raise ExecutionDenied("One to 256 immutable text replacements are required")
    paths = sorted(item.path.casefold() for item in replacements)
    if len(set(paths)) != len(paths) or any(
        right.startswith(left + "/") for left in paths for right in paths
    ):
        raise ExecutionDenied("Duplicate or overlapping replacement paths")
    if (
        sum(len(item.content.encode("utf-8")) for item in replacements)
        > _MAX_EDIT_BYTES
    ):
        raise ExecutionDenied("The replacement data exceeds the edit limit")

    commit = envelope.workspace.commit
    tracked = {
        file.path: file.oid
        for file in repository.committed_files(commit, regular_only=True)
    }
    tracked_names = tuple(path.casefold() for path in tracked)
    differences = []
    for item in sorted(replacements, key=lambda change: change.path):
        if (
            any(char in item.path for char in ("\x00", "\n", "\r", "\t"))
            or "\x00" in item.content
        ):
            raise ExecutionDenied(
                "The text adapter requires printable path boundaries and text content"
            )
        policy.authorize_isolated(
            envelope, context, signed, operation="implement", path=item.path
        )
        from_file = f"a/{item.path}"
        if item.expected_oid is None:
            name = item.path.casefold()
            if any(
                name == existing
                or name.startswith(existing + "/")
                or existing.startswith(name + "/")
                for existing in tracked_names
            ):
                raise ExecutionDenied(
                    "The proposed new file conflicts with a committed path"
                )
            if not item.content:
                raise ExecutionDenied("A new text file requires content")
            current = ""
            from_file = "/dev/null"
        else:
            if tracked.get(item.path) != item.expected_oid:
                raise ExecutionDenied(
                    "The expected committed file version does not match"
                )
            current = repository.read_blob(item.expected_oid, max_bytes=_MAX_EDIT_BYTES)
        if current is None:
            raise ExecutionDenied(
                "The existing file is outside the bounded text adapter"
            )
        differences.extend(
            unified_diff(
                current.splitlines(keepends=True),
                item.content.splitlines(keepends=True),
                fromfile=from_file,
                tofile=f"b/{item.path}",
            )
        )

    diff = "".join(
        line if line.endswith("\n") else f"{line}\n\\ No newline at end of file\n"
        for line in differences
    )
    if not diff or len(diff.encode("utf-8")) > _MAX_DIFF_BYTES:
        raise ExecutionDenied("The review diff is empty or exceeds its byte limit")
    for item in replacements:
        policy.authorize_isolated(
            envelope, context, signed, operation="implement", path=item.path
        )
    binding = json.dumps(
        {
            "commit": commit,
            "replacements": [asdict(item) for item in replacements],
            "diff": diff,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return ChangeReview(commit, replacements, diff, sha256(binding).hexdigest())
