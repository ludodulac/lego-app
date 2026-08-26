import pytest

from brickhouse.building import SourceInfo
from brickhouse.survey.models import (
    ArchitecturalSurvey,
    Certainty,
    ObservationKind,
    PhotoEvidence,
    PhotoView,
    SurveyObservation,
)
from brickhouse.survey.reasoning import (
    QuestionImpact,
    SurveyHypothesis,
    SurveyOpenQuestion,
    SurveyReasoningState,
    rank_questions_for_user_input,
)


def _survey() -> ArchitecturalSurvey:
    source = SourceInfo(kind="user_provided", confidence=1.0)
    return ArchitecturalSurvey(
        id="survey",
        name="test",
        photos=[
            PhotoView(
                photo_index=1,
                facade="front",
                description="front",
                source=source,
                image_left_maps_to_facade_offset="low",
            ),
            PhotoView(
                photo_index=2,
                facade="left",
                description="left",
                source=source,
                image_left_maps_to_facade_offset="low",
            ),
        ],
        observations=[
            SurveyObservation(
                id="roof",
                kind=ObservationKind.ROOF,
                certainty=Certainty.CERTAIN,
                statement="A roof is visible.",
                evidence=[PhotoEvidence(photo_index=1, observation="roof edge visible")],
            )
        ],
    )


def test_open_question_keeps_hypothesis_separate_from_fact() -> None:
    state = SurveyReasoningState(
        survey=_survey(),
        open_questions=[
            SurveyOpenQuestion(
                id="roof_direction",
                question="Which way does the roof fall?",
                subject_observation_ids=["roof"],
                hypotheses=[
                    SurveyHypothesis(
                        statement="It may fall toward the rear.",
                        certainty="plausible",
                        evidence=[PhotoEvidence(photo_index=2, observation="oblique edge suggests a fall")],
                    )
                ],
                impact="blocking",
                resolution_kind="additional_view",
                suggested_evidence="A side/rear view showing both roof edges.",
            )
        ],
    )

    assert state.survey.observations[0].attributes == {}
    assert state.open_questions[0].hypotheses[0].certainty is Certainty.PLAUSIBLE


def test_reasoning_state_rejects_unknown_observation_reference() -> None:
    with pytest.raises(ValueError, match="unknown observations"):
        SurveyReasoningState(
            survey=_survey(),
            open_questions=[
                SurveyOpenQuestion(
                    id="q",
                    question="What is hidden?",
                    subject_observation_ids=["missing"],
                )
            ],
        )


def test_user_questions_are_ranked_by_build_impact() -> None:
    state = SurveyReasoningState(
        survey=_survey(),
        open_questions=[
            SurveyOpenQuestion(id="low", question="Trim detail?", subject_observation_ids=["roof"], impact="low"),
            SurveyOpenQuestion(id="block", question="Roof direction?", subject_observation_ids=["roof"], impact="blocking"),
            SurveyOpenQuestion(id="high", question="Roof type?", subject_observation_ids=["roof"], impact="high"),
        ],
    )

    assert [item.id for item in rank_questions_for_user_input(state)] == ["block", "high", "low"]
    assert state.open_questions[0].impact is QuestionImpact.LOW
