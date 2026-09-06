from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.6}
EVIDENCE = [{"photo_index": 1, "observation": "raised timber platform structure visible"}]


def _survey(*, supports_certainty="certain", guardrail=False):
    attributes = {"supports": ["visible structural support"]}
    attribute_certainty = {"supports": supports_certainty}
    if guardrail:
        attributes["guardrail"] = True
        attribute_certainty["guardrail"] = "certain"
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "terrace-survey",
        "name": "Terrace survey",
        "photos": [{
            "photo_index": 1,
            "facade": "left",
            "description": "left exterior",
            "source": SOURCE,
        }],
        "observations": [{
            "id": "terrace",
            "kind": "platform",
            "facade": "left",
            "certainty": "certain",
            "statement": "raised timber terrace",
            "evidence": EVIDENCE,
            "attributes": attributes,
            "attribute_certainty": attribute_certainty,
        }],
    })


def _scene(*, supports=None, structure=None, edge_treatment=None):
    platform = {
        "id": "terrace",
        "position": {"x": -1.0, "y": 2.0, "z": 1.5},
        "width": 1.0,
        "depth": 2.0,
        "thickness": 0.2,
        "supports": supports or [],
        "material": "timber",
        "source": SOURCE,
    }
    if edge_treatment is not None:
        platform["edge_treatment"] = edge_treatment
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "terrace-scene",
        "name": "Terrace scene",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 8, "source": SOURCE},
            "depth": {"value": 7, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": [platform],
        "platform_structure_observations": structure or [],
        "appearance": {"walls": {"color": "off_white"}},
    })


def _codes(survey, scene):
    return {issue.code for issue in validate_scene_against_survey(survey, scene)}


def test_certain_platform_support_structure_cannot_disappear_from_scene():
    assert "certain_platform_support_structure_lost" in _codes(_survey(), _scene())


def test_unresolved_visible_support_can_survive_as_non_metric_structure_observation():
    scene = _scene(structure=[{
        "id": "terrace-posts-observed",
        "platform_id": "terrace",
        "kind": "vertical_post",
        "statement": "vertical supports are visible but count and coordinates remain unresolved",
        "source": SOURCE,
        "evidence": EVIDENCE,
    }])
    assert "certain_platform_support_structure_lost" not in _codes(_survey(), scene)


def test_resolved_support_post_geometry_also_satisfies_support_preservation():
    scene = _scene(supports=[{
        "id": "post-1",
        "position": {"x": -0.8, "y": 2.2, "z": 0.4},
        "width": 0.2,
        "depth": 0.2,
        "height": 0.8,
        "source": SOURCE,
    }])
    assert "certain_platform_support_structure_lost" not in _codes(_survey(), scene)


def test_plausible_support_attribute_does_not_become_hard_scene_constraint():
    assert "certain_platform_support_structure_lost" not in _codes(
        _survey(supports_certainty="plausible"),
        _scene(),
    )


def test_structured_certain_guardrail_must_survive_without_inventing_exact_edges():
    assert "certain_platform_guardrail_lost" in _codes(_survey(guardrail=True), _scene())
    scene = _scene(structure=[{
        "id": "terrace-guardrail-observed",
        "platform_id": "terrace",
        "kind": "guardrail",
        "statement": "guardrail visible; exact side interruptions remain unresolved",
        "source": SOURCE,
        "evidence": EVIDENCE,
    }])
    codes = _codes(_survey(guardrail=True), scene)
    assert "certain_platform_guardrail_lost" not in codes


def test_global_open_railing_state_preserves_structured_guardrail_when_sides_are_unresolved():
    assert "certain_platform_guardrail_lost" not in _codes(
        _survey(guardrail=True),
        _scene(edge_treatment="open_railing"),
    )
