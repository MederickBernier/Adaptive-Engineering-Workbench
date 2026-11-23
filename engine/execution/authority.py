"""Authenticate scoped grants supplied by a trusted local authorization host."""

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from hmac import compare_digest, digest
from uuid import uuid4

from engine.brain.model import validate_commit
from engine.git.preflight import parse_scope


class ExecutionDenied(PermissionError):
    """An execution request lacks applicable authority or safe state."""


OPERATIONS = frozenset(
    {
        "investigate",
        "implement",
        "run_tests",
        "create_branch",
        "stage",
        "commit",
        "push",
        "create_pr",
        "merge",
    }
)


@dataclass(frozen=True)
class WorkspaceBinding:
    repository: str
    branch: str
    commit: str
    workspace_id: str

    def __post_init__(self) -> None:
        validate_commit(self.commit)
        if not all(
            value.strip() for value in (self.repository, self.branch, self.workspace_id)
        ):
            raise ValueError("Repository, branch, and workspace ID are required")


@dataclass(frozen=True)
class ApprovalGrant:
    grant_id: str
    issuer: str
    task_id: str
    plan_revision: int
    workspace: WorkspaceBinding
    work_units: tuple[str, ...]
    operations: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    review_digest: str | None = None

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.grant_id, self.issuer, self.task_id)
        ):
            raise ValueError("Grant, issuer, and task IDs are required")
        if type(self.plan_revision) is not int or self.plan_revision < 1:
            raise ValueError("A grant requires a positive plan revision")
        if any(
            type(items) is not tuple or any(type(item) is not str for item in items)
            for items in (
                self.work_units,
                self.operations,
                self.allowed_paths,
                self.protected_paths,
            )
        ):
            raise ValueError(
                "Grant scopes and operations must be immutable string tuples"
            )
        if not self.work_units or any(not item.strip() for item in self.work_units):
            raise ValueError("A grant requires explicit Work Unit IDs")
        if not self.operations or set(self.operations) - OPERATIONS:
            raise ValueError("A grant contains missing or unsupported operations")
        if any(
            value.utcoffset() is None for value in (self.issued_at, self.expires_at)
        ):
            raise ValueError("Grant timestamps must include an offset")
        if self.expires_at <= self.issued_at:
            raise ValueError("A grant must expire after issuance")
        for path in (*self.allowed_paths, *self.protected_paths):
            parse_scope(path)


@dataclass(frozen=True)
class SignedGrant:
    grant: ApprovalGrant
    signature: bytes


def _signature(grant: ApprovalGrant, key: bytes) -> bytes:
    payload = asdict(grant)
    payload["issued_at"] = grant.issued_at.isoformat()
    payload["expires_at"] = grant.expires_at.isoformat()
    if grant.review_digest is None:
        del payload["review_digest"]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return digest(key, b"aew-approval-v1\0" + canonical, "sha256")


class TrustedGrantIssuer:
    """Host-side signing interface. Invoke only after trusted human approval."""

    def __init__(self, issuer: str, key: bytes) -> None:
        if not issuer.strip() or len(key) < 32:
            raise ValueError(
                "Grant issuance requires an issuer and at least a 32-byte key"
            )
        self._issuer = issuer
        self._key = bytes(key)

    def issue(
        self,
        *,
        task_id: str,
        plan_revision: int,
        workspace: WorkspaceBinding,
        work_units: tuple[str, ...],
        operations: tuple[str, ...],
        allowed_paths: tuple[str, ...],
        protected_paths: tuple[str, ...] = (),
        issued_at: datetime,
        expires_at: datetime,
        review_digest: str | None = None,
    ) -> SignedGrant:
        grant = ApprovalGrant(
            uuid4().hex,
            self._issuer,
            task_id,
            plan_revision,
            workspace,
            tuple(work_units),
            tuple(operations),
            tuple(allowed_paths),
            tuple(protected_paths),
            issued_at,
            expires_at,
            review_digest,
        )
        return SignedGrant(grant, _signature(grant, self._key))


class GrantVerifier:
    """Verify issuer identity, signed content, lifetime, and live revocation."""

    def __init__(
        self, issuer: str, key: bytes, *, is_revoked: Callable[[str], bool]
    ) -> None:
        if not issuer.strip() or len(key) < 32:
            raise ValueError(
                "Grant verification requires an issuer and at least a 32-byte key"
            )
        self._issuer = issuer
        self._key = bytes(key)
        self._is_revoked = is_revoked

    def verify(self, signed: SignedGrant, *, now: datetime) -> ApprovalGrant:
        grant = signed.grant
        if grant.issuer != self._issuer or not compare_digest(
            signed.signature, _signature(grant, self._key)
        ):
            raise ExecutionDenied("Grant issuer or signature is invalid")
        if not grant.issued_at <= now < grant.expires_at:
            raise ExecutionDenied("Grant is outside its validity interval")
        try:
            revoked = self._is_revoked(grant.grant_id)
        except Exception as error:
            raise ExecutionDenied("Trusted revocation status is unavailable") from error
        if revoked is not False:
            raise ExecutionDenied(
                "Grant is revoked or revocation status is unavailable"
            )
        return grant
