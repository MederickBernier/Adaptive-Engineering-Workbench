"""Evidence-backed planning profile recommendations."""

from dataclasses import dataclass
from enum import StrEnum


class PlanningError(ValueError):
    """A planning input is incomplete or inconsistent."""


class Profile(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    EXPLORE = "explore"


class Level(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class Assessment:
    profile: Profile
    recommended: Profile
    risk: Level
    uncertainty: Level
    rationale: str
    evidence: tuple[str, ...]


def assess(
    *,
    risk: Level,
    uncertainty: Level,
    rationale: str,
    evidence: tuple[str, ...] = (),
    localized: bool = False,
    acceptance_clear: bool = False,
    cross_cutting: bool = False,
    investigation_first: bool = False,
    requested: Profile | None = None,
    override_reason: str | None = None,
) -> Assessment:
    """Recommend a depth from engineer or agent assessment, with no numeric score."""
    if not rationale.strip():
        raise PlanningError("A planning assessment requires a rationale")
    if investigation_first or uncertainty == Level.HIGH:
        recommendation = Profile.EXPLORE
    elif risk == Level.HIGH or cross_cutting:
        recommendation = Profile.DEEP
    elif localized and acceptance_clear and risk == uncertainty == Level.LOW:
        recommendation = Profile.QUICK
    else:
        recommendation = Profile.STANDARD

    if requested is not None and requested != recommendation:
        if recommendation == Profile.EXPLORE:
            raise PlanningError(
                "Investigation must resolve material uncertainty before implementation planning"
            )
        if override_reason is None or not override_reason.strip():
            raise PlanningError("A profile override requires a reason")
        rationale = f"{rationale} Override: {override_reason.strip()}"
    return Assessment(
        requested or recommendation,
        recommendation,
        risk,
        uncertainty,
        rationale,
        tuple(evidence),
    )
