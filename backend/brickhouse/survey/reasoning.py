"""Machine-readable open questions between visual observation and geometry."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArchitecturalSurvey, Certainty, PhotoEvidence


class QuestionImpact(str, Enum):
    """How much resolving a question can change downstream reconstruction."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKING = "blocking"


class SurveyHypothesis(BaseModel):
    """A possible answer that must never be promoted to fact implicitly."""

    statement: str = Field(min_length=1)
    certainty: Certainty = Certainty.UNPROVEN
    evidence: list[PhotoEvidence] = Field(default_factory=list)


class SurveyOpenQuestion(BaseModel):
    """An unresolved question raised by observations from one or more photos."""

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    subject_observation_ids: list[str] = Field(min_length=1)
    hypotheses: list[SurveyHypothesis] = Field(default_factory=list)
    impact: QuestionImpact = QuestionImpact.MEDIUM
    resolution_kind: Literal[
        "additional_view",
        "user_measurement",
        "user_semantic_confirmation",
        "cross_view_fusion",
        "remain_unknown",
    ] = "cross_view_fusion"
    suggested_evidence: str | None = None

    @model_validator(mode="after")
    def validate_subjects(self) -> "SurveyOpenQuestion":
        if len(self.subject_observation_ids) != len(set(self.subject_observation_ids)):
            raise ValueError("open question subject observation IDs must be unique")
        return self


class SurveyReasoningState(BaseModel):
    """Append-only reasoning layer around a validated ArchitecturalSurvey.

    The Survey remains the factual observation record. Questions/hypotheses are
    deliberately separate so an AI can reason about possible geometry without
    contaminating observations with unsupported conclusions.
    """

    schema_version: Literal["0.1"] = "0.1"
    survey: ArchitecturalSurvey
    open_questions: list[SurveyOpenQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "SurveyReasoningState":
        observation_ids = {item.id for item in self.survey.observations}
        question_ids = [item.id for item in self.open_questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("open question IDs must be unique")
        known_photos = {photo.photo_index for photo in self.survey.photos}
        for item in self.open_questions:
            unknown = set(item.subject_observation_ids) - observation_ids
            if unknown:
                raise ValueError(
                    f"open question {item.id!r} references unknown observations: "
                    + ", ".join(sorted(unknown))
                )
            for hypothesis in item.hypotheses:
                for evidence in hypothesis.evidence:
                    if evidence.photo_index not in known_photos:
                        raise ValueError(
                            f"open question {item.id!r} references unknown photo {evidence.photo_index}"
                        )
        return self


def rank_questions_for_user_input(state: SurveyReasoningState) -> list[SurveyOpenQuestion]:
    """Prioritize only questions whose resolution has meaningful build impact."""

    rank = {
        QuestionImpact.BLOCKING: 4,
        QuestionImpact.HIGH: 3,
        QuestionImpact.MEDIUM: 2,
        QuestionImpact.LOW: 1,
    }
    return sorted(state.open_questions, key=lambda item: rank[item.impact], reverse=True)
