"""Resolve required checks against trusted, boundary-specific evidence."""

from dataclasses import dataclass
from enum import StrEnum

from engine.execution.checkpoint import CheckpointStore


class DeliveryError(ValueError):
    """A delivery artifact cannot be prepared from the supplied evidence."""


class VerificationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    NOT_EXECUTED = "not_executed"


@dataclass(frozen=True)
class Verification:
    check: str
    status: VerificationStatus
    execution_id: str
    evidence_id: str | None = None
    reason: str | None = None

    def to_document(self) -> dict[str, str | None]:
        status = self.status.value
        if self.status in (VerificationStatus.SKIPPED, VerificationStatus.UNAVAILABLE):
            status = "incomplete"
        elif self.status == VerificationStatus.NOT_EXECUTED:
            status = "not_run"
        return {
            "check_id": self.check,
            "status": status,
            "execution_id": self.execution_id,
            "evidence_id": self.evidence_id,
            "reason": self.reason,
        }


def resolve_checks(
    store: CheckpointStore,
    *,
    task_id: str,
    plan_revision: int,
    work_unit_id: str,
    repository: str,
    commit: str,
    review_digest: str,
    execution_id: str,
    required: tuple[str, ...],
    evidence_ids: tuple[str, ...] = (),
    omissions: tuple[tuple[str, VerificationStatus, str], ...] = (),
) -> tuple[Verification, ...]:
    results = {}
    for identifier in evidence_ids:
        try:
            item = store.load_check_evidence(identifier)
        except KeyError as error:
            raise DeliveryError(
                "Verification evidence was not observed by the execution store"
            ) from error
        if (
            (
                item.task_id,
                item.plan_revision,
                item.work_unit_id,
                item.repository,
                item.commit,
                item.review_digest,
                item.execution_id,
            )
            != (
                task_id,
                plan_revision,
                work_unit_id,
                repository,
                commit,
                review_digest,
                execution_id,
            )
            or item.check not in required
            or item.check in results
        ):
            raise DeliveryError(
                "Verification evidence does not match the required check and change boundary"
            )
        results[item.check] = Verification(
            item.check,
            VerificationStatus.PASSED
            if item.exit_code == 0
            else VerificationStatus.FAILED,
            execution_id,
            identifier,
            None
            if item.exit_code == 0
            else f"Check exited with status {item.exit_code}.",
        )
    for check, status, reason in omissions:
        if (
            status not in (VerificationStatus.SKIPPED, VerificationStatus.UNAVAILABLE)
            or check not in required
            or check in results
            or not reason.strip()
        ):
            raise DeliveryError(
                "An omission must identify a required check and an explicit reason"
            )
        results[check] = Verification(
            check, status, execution_id, reason=f"{status.value}: {reason}"
        )
    return tuple(
        results.get(
            check, Verification(check, VerificationStatus.NOT_EXECUTED, execution_id)
        )
        for check in dict.fromkeys(required)
    )
