import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene, SceneSurveySeverity, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_scene_real_house_5_v02.json"
SRC = {"kind": "observed", "confidence": 0.9}


def evidence(photo=1, text="observed"):
    return [{"photo_index": photo, "observation": text}]


def opening(oid, facade, h_rank, v_rank, semantic=None, visual=None, photo=1):
    attrs = {"physical_object_count": 1, "facade_horizontal_rank": h_rank, "facade_vertical_rank": v_rank}
    if semantic is not None:
        attrs["semantic_type"] = semantic
    item = {
        "id": oid,
        "kind": "opening",
        "facade": facade,
        "certainty": "certain",
        "statement": oid,
        "evidence": evidence(photo, oid),
        "attributes": attrs,
    }
    if visual is not None:
        item["opening_visual"] = visual
    return item


def _survey():
    front_visual = {"sill": "projecting", "surround_material": "stone_like"}
    observations = [
        {"id":"left_boundary","kind":"building_boundary","facade":"left","certainty":"certain","statement":"left boundary","evidence":evidence(3)},
        opening("front_upper_left_window","front",1,3,"window",front_visual),
        opening("front_upper_right_window","front",2,3,"window",front_visual),
        opening("front_middle_left_window","front",1,2,"window",front_visual),
        opening("front_middle_right_window","front",2,2,"window",front_visual),
        opening("front_low_left_window","front",1,1,"window",{"surround_material":"stone_like"}),
        opening("front_glazed_access","front",2,1,"door_or_glazed_door",None),
        opening("right_upper_window","right",1,2,"window",None,2),
        opening("right_low_window","right",2,1,"window",None,2),
        opening("left_upper_window","left",1,2,"window",None,3),
        opening("left_mid_opening","left",1,1,None,None,3),
        {"id":"main_gable_roof","kind":"roof","facade":"front","certainty":"certain","statement":"front gable roof","evidence":evidence(1),"attributes":{"roof_type":"gable","facade_is_gable":True},"attribute_certainty":{"roof_type":"certain","facade_is_gable":"certain"}},
        {"id":"right_rising_road","kind":"terrain","facade":"right","certainty":"certain","statement":"grade rises","evidence":evidence(2),"attributes":{"slope_direction":"front_to_rear_rising"},"attribute_certainty":{"slope_direction":"certain"}},
        {"id":"chimney_front_left","kind":"chimney","facade":"front","certainty":"certain","statement":"chimney","evidence":evidence(1)},
        {"id":"chimney_rear_area","kind":"chimney","facade":"rear","certainty":"certain","statement":"rear chimney","evidence":evidence(5)},
        {"id":"left_timber_terrace","kind":"platform","facade":"left","certainty":"certain","statement":"timber terrace","evidence":evidence(3),"attributes":{"exterior_material":"timber"}},
        {"id":"left_exterior_stair","kind":"stair","facade":"left","certainty":"certain","statement":"concrete stair","evidence":evidence(4),"attributes":{"exterior_material":"concrete"}},
        {"id":"left_lower_structure","kind":"volume","facade":"left","certainty":"certain","statement":"secondary exterior structure","evidence":evidence(4)},
    ]
    return ArchitecturalSurvey.model_validate({
        "schema_version":"0.1",
        "id":"survey_real_house_5_v04",
        "name":"Maison réelle — relevé conservateur 5 photos",
        "photos":[
            {"photo_index":1,"facade":"front","description":"front","source":SRC},
            {"photo_index":2,"facade":"right","description":"right","source":SRC},
            {"photo_index":3,"facade":"left","description":"left","source":SRC},
            {"photo_index":4,"facade":"left","description":"left 2","source":SRC},
            {"photo_index":5,"facade":"rear","description":"rear","source":SRC},
        ],
        "known_measurements":[{"kind":"front_width","value":10.0,"units":"m","source":{"kind":"user_provided","confidence":0.99}}],
        "observations":observations,
        "relations":[
            {"id":"rel_terrace_building","kind":"connects_to","subject_id":"left_timber_terrace","object_id":"left_boundary","certainty":"certain","statement":"terrace connects","evidence":evidence(3)},
            {"id":"rel_stair_building","kind":"connects_to","subject_id":"left_exterior_stair","object_id":"left_boundary","certainty":"certain","statement":"stair connects","evidence":evidence(4)},
            {"id":"rel_lower_structure_building","kind":"adjacent_to","subject_id":"left_lower_structure","object_id":"left_boundary","certainty":"certain","statement":"structure adjacent","evidence":evidence(4)},
        ],
    })


def test_real_house_5_scene_is_faithful_to_validated_survey_contract():
    scene = ArchitecturalScene.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    issues = validate_scene_against_survey(_survey(), scene)
    errors = [issue for issue in issues if issue.severity is SceneSurveySeverity.ERROR]
    assert errors == [], [(issue.code, issue.object_id, issue.message) for issue in errors]
    assert {relation.id for relation in scene.relations} == {
        "rel_terrace_building",
        "rel_stair_building",
        "rel_lower_structure_building",
    }
