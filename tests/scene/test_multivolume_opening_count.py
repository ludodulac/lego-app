from types import SimpleNamespace

from brickhouse.building import Facade
from brickhouse.scene.topology_fidelity import _facade_opening_counts_match_by_survey_identity
from brickhouse.survey import Certainty, ObservationKind


def _survey_opening(object_id: str, facade: Facade, *, host_object: str | None = None):
    attributes = {}
    if host_object is not None:
        attributes["host_object"] = host_object
    return SimpleNamespace(
        id=object_id,
        kind=ObservationKind.OPENING,
        certainty=Certainty.CERTAIN,
        facade=facade,
        attributes=attributes,
    )


def _scene_opening(object_id: str, facade: Facade, volume_id: str):
    return SimpleNamespace(id=object_id, facade=facade, volume_id=volume_id)


def test_facade_count_uses_survey_identity_not_first_scene_volume() -> None:
    survey = SimpleNamespace(
        observations=[
            _survey_opening("left_lower", Facade.LEFT),
            _survey_opening("left_upper", Facade.LEFT),
        ]
    )
    scene = SimpleNamespace(
        openings=[
            _scene_opening("left_lower", Facade.LEFT, "secondary_volume"),
            _scene_opening("left_upper", Facade.LEFT, "volume_main"),
        ]
    )

    assert _facade_opening_counts_match_by_survey_identity(survey, scene)


def test_facade_count_still_detects_real_missing_certain_opening() -> None:
    survey = SimpleNamespace(
        observations=[
            _survey_opening("left_lower", Facade.LEFT),
            _survey_opening("left_upper", Facade.LEFT),
        ]
    )
    scene = SimpleNamespace(openings=[_scene_opening("left_upper", Facade.LEFT, "volume_main")])

    assert not _facade_opening_counts_match_by_survey_identity(survey, scene)


def test_secondary_host_semantics_are_excluded_on_both_sides() -> None:
    survey = SimpleNamespace(
        observations=[
            _survey_opening("main_left", Facade.LEFT),
            _survey_opening("annex_left", Facade.LEFT, host_object="annex"),
        ]
    )
    scene = SimpleNamespace(
        openings=[
            _scene_opening("main_left", Facade.LEFT, "secondary_volume"),
            _scene_opening("annex_left", Facade.LEFT, "annex"),
        ]
    )

    assert _facade_opening_counts_match_by_survey_identity(survey, scene)
