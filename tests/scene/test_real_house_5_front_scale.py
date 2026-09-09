import json
from copy import deepcopy
from pathlib import Path

import pytest

from brickhouse.scene import (
    ArchitecturalScene,
    OpeningPriorQuery,
    PhotoGeometryAnnotation,
    PhotoScaleCueBinding,
    PlanarPhotoRectification,
    build_visual_scale_cues_from_photo_geometry,
    estimate_architectural_scale,
    france_residential_opening_priors_v01,
    rectified_plane_reference_annotation,
    rectify_photo_geometry_annotation,
)
from brickhouse.survey import ArchitecturalSurvey


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SURVEY_PATH = BENCHMARK / "accepted-survey-v0.1.json"
EVIDENCE_PATH = BENCHMARK / "front-width-scale-evidence.json"
ESTIMATE_PATH = BENCHMARK / "front-width-scale-estimate.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _estimate_from_sidecar():
    survey = ArchitecturalSurvey.model_validate(_load(SURVEY_PATH))
    evidence = _load(EVIDENCE_PATH)
    before = deepcopy(survey.model_dump())

    rectification = PlanarPhotoRectification.model_validate(evidence["rectification"])
    annotations = [
        PhotoGeometryAnnotation.model_validate(item)
        for item in evidence["annotations"]
    ]
    rectified = [
        rectify_photo_geometry_annotation(rectification, item)
        for item in annotations
    ]
    rectified_by_source_id = {
        source.id: item for source, item in zip(annotations, rectified, strict=True)
    }
    reference = rectified_plane_reference_annotation(
        rectification,
        annotation_id="real-house-5-front-wall-reference-v1",
        observation_id="building-boundary-1",
        statement="Rectified benchmark front wall reference plane.",
    )
    reference_extent = evidence["reference_extent"]

    priors_by_id = {}
    bindings = []
    for spec in evidence["cue_specs"]:
        query = OpeningPriorQuery(
            semantic_type=spec["semantic_type"],
            leaf_count=spec["leaf_count"],
        )
        for prior in france_residential_opening_priors_v01(query):
            if prior.dimension == "width":
                priors_by_id[prior.id] = prior
        feature = rectified_by_source_id[spec["annotation_id"]]
        bindings.append(
            PhotoScaleCueBinding(
                id=f"{feature.id}:width",
                feature_annotation_id=feature.id,
                reference_annotation_id=reference.id,
                axis="width",
                cue_family=spec["cue_family"],
                prior_id=spec["prior_id"],
                reference_extent_coverage=reference_extent["coverage"],
                target_extent_id=reference_extent["target_extent_id"],
            )
        )

    cues = build_visual_scale_cues_from_photo_geometry(
        survey,
        [*rectified, reference],
        bindings,
    )
    estimate = estimate_architectural_scale(
        cues,
        list(priors_by_id.values()),
        minimum_independent_families=evidence["policy"]["minimum_independent_families"],
    )

    assert survey.model_dump() == before
    assert survey.known_measurements == []
    return survey, estimate


def test_front_width_is_resolved_without_user_measurement() -> None:
    _, estimate = _estimate_from_sidecar()

    assert estimate.resolved is True
    assert estimate.source.kind.value == "inferred"
    assert estimate.supporting_families == [
        "front_glazed_door_width",
        "front_repeated_window_width",
        "front_small_window_width",
    ]
    assert len(estimate.supporting_cue_ids) == 6
    assert estimate.rejected_cue_ids == []
    assert estimate.max_m - estimate.min_m > 1.0
    assert 0 < estimate.confidence < 0.5


def test_front_width_sidecar_explicitly_proves_reference_extent_identity() -> None:
    evidence = _load(EVIDENCE_PATH)

    assert evidence["reference_extent"]["coverage"] == "full_target_extent"
    assert evidence["reference_extent"]["target_extent_id"] == evidence["target"]


def test_serialized_front_width_estimate_matches_reproducible_inference() -> None:
    _, estimate = _estimate_from_sidecar()
    stored = _load(ESTIMATE_PATH)

    assert stored["source"]["kind"] == "inferred"
    assert stored["survey_invariants"]["known_measurements_count"] == 0
    assert stored["value_m"] == pytest.approx(estimate.value_m, abs=0.001)
    assert stored["min_m"] == pytest.approx(estimate.min_m, abs=0.001)
    assert stored["max_m"] == pytest.approx(estimate.max_m, abs=0.001)
    assert stored["confidence"] == pytest.approx(estimate.confidence, abs=0.001)
    assert stored["supporting_families"] == estimate.supporting_families
    assert stored["supporting_cue_ids"] == estimate.supporting_cue_ids
    assert stored["rejected_cue_ids"] == estimate.rejected_cue_ids


def test_existing_scene_width_is_retained_when_inside_new_interval() -> None:
    survey, estimate = _estimate_from_sidecar()
    scene = ArchitecturalScene.model_validate(_load(SCENE_PATH))
    stored = _load(ESTIMATE_PATH)

    width = scene.volumes[0].width
    assert survey.known_measurements == []
    assert width.source.kind.value == "inferred"
    assert width.value == pytest.approx(stored["existing_scene_candidate"]["width_m"])
    assert estimate.min_m <= width.value <= estimate.max_m
    assert stored["existing_scene_candidate"]["inside_estimated_interval"] is True
    assert stored["existing_scene_candidate"]["action"] == "retain"
