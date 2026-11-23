import pytest

from engine.planning.assessment import Level, PlanningError, Profile, assess


@pytest.mark.parametrize(
    ("inputs", "profile"),
    [
        ({"localized": True, "acceptance_clear": True}, Profile.QUICK),
        ({"localized": True}, Profile.STANDARD),
        ({"cross_cutting": True}, Profile.DEEP),
        (
            {"risk": Level.HIGH, "localized": True, "acceptance_clear": True},
            Profile.DEEP,
        ),
        ({"investigation_first": True}, Profile.EXPLORE),
        ({"uncertainty": Level.HIGH}, Profile.EXPLORE),
    ],
)
def test_profile_recommendation(inputs: dict, profile: Profile) -> None:
    assessment = assess(
        **({"risk": Level.LOW, "uncertainty": Level.LOW} | inputs),
        rationale="Observed task scope",
        evidence=("context:verified",),
    )
    assert assessment.profile == assessment.recommended == profile
    assert assessment.evidence == ("context:verified",)


def test_profile_override_preserves_recommendation_and_reason() -> None:
    assessment = assess(
        risk=Level.LOW,
        uncertainty=Level.LOW,
        rationale="Bounded change",
        requested=Profile.DEEP,
        override_reason="Engineer requests additional review",
    )
    assert assessment.recommended == Profile.STANDARD
    assert assessment.profile == Profile.DEEP
    assert "additional review" in assessment.rationale


def test_unresolved_exploration_cannot_be_overridden_into_implementation() -> None:
    with pytest.raises(PlanningError, match="resolve material uncertainty"):
        assess(
            risk=Level.MODERATE,
            uncertainty=Level.HIGH,
            rationale="Source behavior unknown",
            requested=Profile.QUICK,
            override_reason="Try a small change",
        )
