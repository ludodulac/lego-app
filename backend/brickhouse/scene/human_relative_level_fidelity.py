"""Audit metric Scene platform levels against non-metric user ordering facts."""
from __future__ import annotations
from pydantic import BaseModel, Field
from brickhouse.survey import ArchitecturalSurvey, Certainty
from brickhouse.survey.human_spatial_facts import HumanRelativeLevelFact
from .wall_profile_scene import ArchitecturalScene
_LEVEL_EPSILON_M = 1e-6
class HumanRelativeLevelIssue(BaseModel):
    code: str
    subject_id: str
    object_id: str
    message: str
class HumanRelativeLevelReport(BaseModel):
    issues: list[HumanRelativeLevelIssue] = Field(default_factory=list)
def _scene_level(scene: ArchitecturalScene, observation_id: str) -> float | None:
    platform = next((item for item in scene.platforms if item.id == observation_id), None)
    return platform.position.z if platform is not None else None
def validate_scene_against_human_relative_level_facts(survey: ArchitecturalSurvey, scene: ArchitecturalScene, facts: list[HumanRelativeLevelFact]) -> HumanRelativeLevelReport:
    """Reject only proven contradictions; never invent a metric separation."""
    observation_ids = {item.id for item in survey.observations}
    issues: list[HumanRelativeLevelIssue] = []
    for fact in facts:
        if fact.certainty is not Certainty.CERTAIN: continue
        if fact.subject_observation_id not in observation_ids or fact.object_observation_id not in observation_ids:
            raise ValueError("human relative-level fact must be validated against this Survey before Scene audit")
        subject_level = _scene_level(scene, fact.subject_observation_id)
        object_level = _scene_level(scene, fact.object_observation_id)
        if subject_level is None or object_level is None: continue
        contradiction = ((fact.relation == "lower_than" and not subject_level < object_level - _LEVEL_EPSILON_M) or (fact.relation == "higher_than" and not subject_level > object_level + _LEVEL_EPSILON_M) or (fact.relation == "same_level" and abs(subject_level - object_level) > _LEVEL_EPSILON_M))
        if contradiction:
            issues.append(HumanRelativeLevelIssue(code="human_relative_level_contradicted", subject_id=fact.subject_observation_id, object_id=fact.object_observation_id, message=f"Scene platform levels contradict user-provided relation {fact.subject_observation_id!r} {fact.relation} {fact.object_observation_id!r}; no default vertical separation may be invented."))
    return HumanRelativeLevelReport(issues=issues)
