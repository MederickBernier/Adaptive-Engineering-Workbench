from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from engine.execution.authority import (
    ExecutionDenied,
    GrantVerifier,
    TrustedGrantIssuer,
    WorkspaceBinding,
)

KEY = b"k" * 32
NOW = datetime(2026, 1, 1, tzinfo=UTC)
WORKSPACE = WorkspaceBinding("example/project", "master", "a" * 40, "checkout")


def grant():
    return TrustedGrantIssuer("engineer", KEY).issue(
        task_id="task-1",
        plan_revision=1,
        workspace=WORKSPACE,
        work_units=("unit-1",),
        operations=("investigate",),
        allowed_paths=("src/**",),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )


def test_signed_grant_requires_trusted_issuer_and_unchanged_content() -> None:
    signed = grant()
    verifier = GrantVerifier("engineer", KEY, is_revoked=lambda _: False)
    assert verifier.verify(signed, now=NOW) == signed.grant
    forged = replace(signed, grant=replace(signed.grant, operations=("implement",)))
    with pytest.raises(ExecutionDenied, match="signature"):
        verifier.verify(forged, now=NOW)
    with pytest.raises(ExecutionDenied, match="issuer"):
        GrantVerifier("other", KEY, is_revoked=lambda _: False).verify(signed, now=NOW)


def test_expired_or_revoked_grants_are_denied() -> None:
    signed = grant()
    verifier = GrantVerifier("engineer", KEY, is_revoked=lambda _: False)
    with pytest.raises(ExecutionDenied, match="validity interval"):
        verifier.verify(signed, now=signed.grant.expires_at)
    with pytest.raises(ExecutionDenied, match="revoked"):
        GrantVerifier("engineer", KEY, is_revoked=lambda _: True).verify(
            signed, now=NOW
        )


def test_unavailable_revocation_is_fail_closed() -> None:
    def unavailable(_grant_id: str) -> bool:
        raise OSError("Store unavailable")

    with pytest.raises(ExecutionDenied, match="revocation status is unavailable"):
        GrantVerifier("engineer", KEY, is_revoked=unavailable).verify(grant(), now=NOW)
