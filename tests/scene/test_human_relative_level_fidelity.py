from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.human_relative_level_fidelity import validate_scene_against_human_relative_level_facts
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_spatial_facts import HumanRelativeLevelFact

SOURCE = {"kind": "inferred", "confidence": 0.7}
USER = {"kind": "user_provided", "confidence": 1.0}

def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1", "id": "generic-level-fidelity-survey", "name": "Generic level fidelity survey",
        "photos": [{"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE}],
        "observations": [
            {"id": "deck-a", "kind": "platform", "certainty": "certain", "statement": "deck", "evidence": [{"photo_index": 1, "observation": "deck"}]},
            {"id": "landing-b", "kind": "platform", "certainty": "certain", "statement": "landing", "evidence": [{"photo_index": 1, "observation": "landing"}]},
        ],
    })

def _scene(deck_z: float, landing_z: float) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2", "id": "generic-level-fidelity-scene", "name": "Generic level fidelity scene", "units": "m",
        "volumes": [{"id": "host", "position": {"x": 0, "y": 0, "z": 0}, "width": {"value": 6, "source": SOURCE}, "depth": {"value": 6, "source": SOURCE}, "height": {"value": 5, "source": SOURCE}, "floors": 2, "source": SOURCE}],
        "platforms": [
            {"id": "deck-a", "host_volume_id": "host", "position": {"x": -1, "y": 1, "z": deck_z}, "width": 1, "depth": 1, "thickness": 0.2, "source": SOURCE},
            {"id": "landing-b", "host_volume_id": "host", "position": {"x": 6, "y": 2, "z": landing_z}, "width": 1, "depth": 1, "thickness": 0.2, "source": SOURCE},
        ],
        "relations": [
            {"id": "deck-host", "kind": "connects_to", "subject_id": "deck-a", "object_id": "host", "certainty": "certain", "geometry_status": "resolved", "statement": "deck touches host"},
            {"id": "landing-host", "kind": "connects_to", "subject_id": "landing-b", "object_id": "host", "certainty": "certain", "geometry_status": "resolved", "statement": "landing touches host"},
        ],
        "appearance": {},
    })

def _fact() -> HumanRelativeLevelFact:
    return HumanRelativeLevelFact.model_validate({"subject_observation_id": "deck-a", "object_observation_id": "landing-b", "relation": "lower_than", "certainty": "certain", "source": USER, "statement": "Deck is lower than landing; no metric delta supplied."})

def test_any_positive_separation_satisfies_non_metric_lower_than_fact() -> None:
    assert validate_scene_against_human_relative_level_facts(_survey(), _scene(2.0, 2.01), [_fact()]).issues == []

def test_equal_or_reversed_levels_contradict_certain_user_ordering() -> None:
    equal = validate_scene_against_human_relative_level_facts(_survey(), _scene(2.0, 2.0), [_fact()])
    reversed_levels = validate_scene_against_human_relative_level_facts(_survey(), _scene(2.1, 2.0), [_fact()])
    assert [issue.code for issue in equal.issues] == ["human_relative_level_contradicted"]
    assert [issue.code for issue in reversed_levels.issues] == ["human_relative_level_contradicted"]
