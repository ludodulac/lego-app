import pytest

from brickhouse.building import SourceKind
from brickhouse.scene import (
    ArchitecturalDimensionPrior,
    ArchitecturalPriorProvenance,
    PhotoGeometryAnnotation,
    PhotoScaleCueBinding,
    build_visual_scale_cues_from_photo_geometry,
    estimate_architectural_scale,
)
from brickhouse.survey import ArchitecturalSurvey


def test_explicit_photo_regions_feed_multi_family_scale_consensus_without_measurement() -> None:
    survey = ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-scale-bridge-house",
            "name": "Generic scale bridge house",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "Canonical front view with envelope and openings.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                }
            ],
            "known_measurements": [],
            "observations": [
                {
                    "id": "front-envelope",
                    "kind": "building_boundary",
                    "certainty": "certain",
                    "statement": "Front envelope is visible.",
                    "evidence": [{"photo_index": 1, "observation": "Visible facade envelope."}],
                },
                {
                    "id": "front-window",
                    "kind": "opening",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "Window is visible.",
                    "evidence": [{"photo_index": 1, "observation": "Visible window."}],
                    "attributes": {"semantic_type": "window"},
                    "attribute_certainty": {"semantic_type": "certain"},
                },
                {
                    "id": "front-door",
                    "kind": "opening",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "Door is visible.",
                    "evidence": [{"photo_index": 1, "observation": "Visible door."}],
                    "attributes": {"semantic_type": "door"},
                    "attribute_certainty": {"semantic_type": "certain"},
                },
            ],
        }
    )
    annotations = [
        PhotoGeometryAnnotation(
            id="front-envelope-box",
            observation_id="front-envelope",
            photo_index=1,
            region={"x0": 0.10, "y0": 0.10, "x1": 0.90, "y1": 0.90},
            source={"kind": "inferred", "confidence": 0.90},
            statement="Vision-estimated visible facade bounds.",
        ),
        PhotoGeometryAnnotation(
            id="front-window-box",
            observation_id="front-window",
            photo_index=1,
            region={"x0": 0.25, "y0": 0.30, "x1": 0.35, "y1": 0.62},
            source={"kind": "inferred", "confidence": 0.82},
            statement="Vision-estimated window bounds.",
        ),
        PhotoGeometryAnnotation(
            id="front-door-box",
            observation_id="front-door",
            photo_index=1,
            region={"x0": 0.65, "y0": 0.50, "x1": 0.73, "y1": 0.88},
            source={"kind": "inferred", "confidence": 0.84},
            statement="Vision-estimated door bounds.",
        ),
    ]
    bindings = [
        PhotoScaleCueBinding(
            id="window-width-cue",
            feature_annotation_id="front-window-box",
            reference_annotation_id="front-envelope-box",
            axis="width",
            cue_family="window_width",
            prior_id="window-width-prior",
        ),
        PhotoScaleCueBinding(
            id="door-width-cue",
            feature_annotation_id="front-door-box",
            reference_annotation_id="front-envelope-box",
            axis="width",
            cue_family="door_width",
            prior_id="door-width-prior",
        ),
    ]
    priors = [
        ArchitecturalDimensionPrior(
            id="window-width-prior",
            feature_kind="window",
            dimension="width",
            min_m=1.0,
            max_m=1.2,
            typical_m=1.1,
            confidence=0.65,
            provenance=ArchitecturalPriorProvenance(
                reference="generic anonymized window prior",
                context="test fixture",
            ),
        ),
        ArchitecturalDimensionPrior(
            id="door-width-prior",
            feature_kind="door",
            dimension="width",
            min_m=0.8,
            max_m=0.95,
            typical_m=0.88,
            confidence=0.65,
            provenance=ArchitecturalPriorProvenance(
                reference="generic anonymized door prior",
                context="test fixture",
            ),
        ),
    ]

    cues = build_visual_scale_cues_from_photo_geometry(survey, annotations, bindings)
    estimate = estimate_architectural_scale(cues, priors)

    assert survey.known_measurements == []
    assert [cue.normalized_extent for cue in cues] == pytest.approx([0.125, 0.10])
    assert estimate.resolved is True
    assert estimate.source.kind is SourceKind.INFERRED
    assert estimate.value_m == pytest.approx(8.8, abs=0.2)
    assert estimate.min_m == pytest.approx(8.0)
    assert estimate.max_m == pytest.approx(9.5)
    assert estimate.min_m <= estimate.value_m <= estimate.max_m
    assert set(estimate.supporting_families) == {"window_width", "door_width"}
