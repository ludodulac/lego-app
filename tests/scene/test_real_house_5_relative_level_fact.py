import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.human_relative_level_fidelity import validate_scene_against_human_relative_level_facts
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_spatial_facts import HumanRelativeLevelFact, validate_human_relative_level_facts


ROOT = Path(__file__).resolve().parents[2]
SURVEY_PATH = ROOT / "frontend" / "benchmarks" / "real-house-5" / "accepted-survey-v0.1.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"


def test_user_confirmed_timber_deck_lower_than_massive_landing_exposes_current_scene_defect() -> None:
    survey = ArchitecturalSurvey.model_validate(json.loads(SURVEY_PATH.read_text(encoding="utf-8")))
    scene = ArchitecturalScene.model_validate(json.loads(SCENE_PATH.read_text(encoding="utf-8")))
    fact = HumanRelativeLevelFact.model_validate(
        {
            "subject_observation_id": "platform-timber-1",
            "object_observation_id": "platform-massive-1",
            "relation": "lower_than",
            "certainty": "certain",
            "source": {"kind": "user_provided", "confidence": 1.0},
            "statement": "User confirms the timber deck walking surface is lower than the massive stair-arrival landing.",
        }
    )

    validated = validate_human_relative_level_facts(survey, [fact])
    report = validate_scene_against_human_relative_level_facts(survey, scene, validated.facts)

    timber = next(item for item in scene.platforms if item.id == "platform-timber-1")
    landing = next(item for item in scene.platforms if item.id == "platform-massive-1")
    assert survey.known_measurements == []
    assert timber.position.z == landing.position.z
    assert [issue.code for issue in report.issues] == ["human_relative_level_contradicted"]
