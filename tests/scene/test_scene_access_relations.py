from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.7}


def _survey():
    return ArchitecturalSurvey.model_validate({
        "schema_version":"0.1","id":"survey-access","name":"Access relation",
        "photos":[{"photo_index":1,"facade":"front","description":"front","source":SOURCE},{"photo_index":2,"facade":"right","description":"right","source":SOURCE}],
        "observations":[
            {"id":"deck","kind":"platform","facade":"right","certainty":"certain","statement":"deck","evidence":[{"photo_index":2,"observation":"visible"}]},
            {"id":"stair","kind":"stair","facade":"right","certainty":"certain","statement":"stair","evidence":[{"photo_index":2,"observation":"visible"}]},
        ],
        "relations":[{"id":"stair_to_deck","kind":"connects_to","subject_id":"stair","object_id":"deck","certainty":"certain","statement":"stair reaches deck","evidence":[{"photo_index":2,"observation":"stair ends at deck edge"}]}],
    })


def _scene(access_spans):
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"scene-access","name":"Access scene","units":"m",
        "volumes":[{"id":"main","position":{"x":0,"y":0,"z":0},"width":{"value":10,"source":SOURCE},"depth":{"value":8,"source":SOURCE},"height":{"value":6,"source":SOURCE},"floors":2,"source":SOURCE}],
        "platforms":[{"id":"deck","position":{"x":10,"y":2,"z":1},"width":2,"depth":2,"thickness":.2,"supports":[],"edges":{"x_max":{"treatment":"open_railing","access_spans":access_spans}},"source":SOURCE}],
        "stairs":[{"id":"stair","start":{"x":14,"y":3,"z":0},"end":{"x":12,"y":3,"z":1},"width":1,"source":SOURCE}],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def test_certain_stair_connection_is_blocked_by_continuous_railing():
    codes={issue.code for issue in validate_scene_against_survey(_survey(),_scene([]))}
    assert "certain_connection_blocked_by_platform_edge" in codes


def test_certain_stair_connection_passes_through_declared_access_span():
    codes={issue.code for issue in validate_scene_against_survey(_survey(),_scene([{"from":.5,"to":1.5}]))}
    assert "certain_connection_blocked_by_platform_edge" not in codes
    assert "certain_connection_broken" not in codes


def _platform_survey():
    return ArchitecturalSurvey.model_validate({
        "schema_version":"0.1","id":"survey-platform-transition","name":"Platform transition",
        "photos":[{"photo_index":1,"facade":"front","description":"front","source":SOURCE},{"photo_index":2,"facade":"right","description":"right","source":SOURCE}],
        "observations":[
            {"id":"landing","kind":"platform","facade":"right","certainty":"certain","statement":"concrete landing","evidence":[{"photo_index":2,"observation":"landing visible"}]},
            {"id":"deck","kind":"platform","facade":"right","certainty":"certain","statement":"timber deck","evidence":[{"photo_index":2,"observation":"deck visible"}]},
        ],
        "relations":[{"id":"landing_to_deck","kind":"connects_to","subject_id":"landing","object_id":"deck","certainty":"certain","statement":"landing opens directly onto deck","evidence":[{"photo_index":2,"observation":"shared transition visible"}]}],
    })


def _platform_scene(*,landing_access=False):
    landing_edge={"treatment":"solid_parapet","access_spans":[{"from":0,"to":2}]} if landing_access else {"treatment":"solid_parapet","access_spans":[]}
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"scene-platform-transition","name":"Platform transition","units":"m",
        "volumes":[{"id":"main","position":{"x":0,"y":0,"z":0},"width":{"value":10,"source":SOURCE},"depth":{"value":8,"source":SOURCE},"height":{"value":6,"source":SOURCE},"floors":2,"source":SOURCE}],
        "platforms":[
            {"id":"landing","position":{"x":10,"y":2,"z":1.2},"width":2,"depth":2,"thickness":.25,"material":"concrete","edges":{"y_max":landing_edge},"source":SOURCE},
            {"id":"deck","position":{"x":10,"y":4,"z":1.2},"width":2,"depth":2,"thickness":.2,"material":"timber","edges":{"y_min":{"treatment":"none"}},"source":SOURCE},
        ],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def test_certain_platform_transition_is_blocked_by_continuous_parapet():
    codes={issue.code for issue in validate_scene_against_survey(_platform_survey(),_platform_scene())}
    assert "certain_platform_transition_blocked" in codes


def test_certain_platform_transition_passes_through_full_declared_opening():
    codes={issue.code for issue in validate_scene_against_survey(_platform_survey(),_platform_scene(landing_access=True))}
    assert "certain_platform_transition_blocked" not in codes
    assert "certain_connection_broken" not in codes
