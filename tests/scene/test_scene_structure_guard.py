from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey(
    *,
    include_platform=True,
    platform_certainty="plausible",
    include_grade=False,
    grade_certainty="certain",
) -> ArchitecturalSurvey:
    observations = []
    if include_platform:
        observations.append({
            "id": "deck",
            "kind": "platform",
            "facade": "right",
            "certainty": platform_certainty,
            "statement": "Raised exterior deck visible on the right side.",
            "evidence": [{"photo_index": 2, "observation": "Deck edge visible."}],
        })
    if include_grade:
        observations.append({
            "id": "right-grade",
            "kind": "terrain",
            "facade": "right",
            "certainty": grade_certainty,
            "statement": "Ground level rises along the right facade.",
            "evidence": [{"photo_index": 2, "observation": "Street/ground edge visibly rises along the wall."}],
            "attributes": {"slope_direction": "low_to_high"},
        })
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "structure-guard-survey",
        "name": "Structure guard",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE},
            {"photo_index": 2, "facade": "right", "description": "side", "source": SOURCE},
        ],
        "observations": observations,
    })


def _scene(
    *,
    confidence=0.6,
    source_kind="inferred",
    include_grade=False,
    grade_confidence=0.6,
    grade_source_kind="inferred",
) -> ArchitecturalScene:
    data = {
        "schema_version": "0.2",
        "id": "structure-guard-scene",
        "name": "Structure guard scene",
        "units": "m",
        "volumes": [{
            "id": "main", "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE}, "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE}, "floors": 2, "source": SOURCE,
        }],
        "platforms": [{
            "id": "deck", "host_volume_id": "main", "position": {"x": 10, "y": 2, "z": 1.5},
            "width": 1.5, "depth": 2, "thickness": 0.2, "material": "timber",
            "source": {"kind": source_kind, "confidence": confidence},
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
    }
    if include_grade:
        data["terrain"] = {
            "kind": "facade_grade_profiles",
            "profiles": [{
                "facade": "right",
                "start_elevation": 0.0,
                "end_elevation": 0.8,
                "outward_extent": 1.2,
                "source": {"kind": grade_source_kind, "confidence": grade_confidence},
            }],
        }
    return ArchitecturalScene.model_validate(data)


def test_scene_cannot_invent_platform_absent_from_validated_survey() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(include_platform=False), _scene())}
    assert "scene_platform_not_in_survey" in codes


def test_unproven_platform_cannot_be_promoted_to_scene_geometry() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(platform_certainty="unproven"), _scene())}
    assert "unproven_platform_promoted" in codes


def test_plausible_platform_must_not_claim_high_metric_confidence() -> None:
    issues = validate_scene_against_survey(_survey(platform_certainty="plausible"), _scene(confidence=0.9))
    matches = [issue for issue in issues if issue.code == "plausible_platform_overconfidence"]
    assert len(matches) == 1
    assert matches[0].severity.value == "error"


def test_exterior_platform_geometry_cannot_be_generated_default() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(platform_certainty="certain"),
        _scene(confidence=0.4, source_kind="generated_default"),
    )}
    assert "platform_generated_default_geometry" in codes


def test_plausible_platform_with_conservative_confidence_remains_allowed() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(_survey(platform_certainty="plausible"), _scene(confidence=0.6))}
    assert "scene_platform_not_in_survey" not in codes
    assert "unproven_platform_promoted" not in codes
    assert "plausible_platform_overconfidence" not in codes


def test_scene_cannot_invent_grade_profile_absent_from_survey() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(include_grade=False),
        _scene(include_grade=True),
    )}
    assert "scene_grade_not_in_survey" in codes


def test_unproven_grade_cannot_be_promoted_to_metric_terrain() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(include_grade=True, grade_certainty="unproven"),
        _scene(include_grade=True),
    )}
    assert "unproven_grade_promoted" in codes


def test_plausible_grade_must_keep_conservative_metric_confidence() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(include_grade=True, grade_certainty="plausible"),
        _scene(include_grade=True, grade_confidence=0.9),
    )}
    assert "plausible_grade_overconfidence" in codes


def test_grade_profile_geometry_cannot_be_generated_default() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(include_grade=True, grade_certainty="certain"),
        _scene(include_grade=True, grade_confidence=0.4, grade_source_kind="generated_default"),
    )}
    assert "grade_generated_default_geometry" in codes


def test_plausible_grade_with_conservative_confidence_remains_allowed() -> None:
    codes = {issue.code for issue in validate_scene_against_survey(
        _survey(include_grade=True, grade_certainty="plausible"),
        _scene(include_grade=True, grade_confidence=0.6),
    )}
    assert "scene_grade_not_in_survey" not in codes
    assert "unproven_grade_promoted" not in codes
    assert "plausible_grade_overconfidence" not in codes
