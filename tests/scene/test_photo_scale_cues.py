from copy import deepcopy

import pytest

from brickhouse.scene.photo_scale_cues import (
    PhotoGeometryAnnotation,
    PhotoScaleCueBinding,
    build_visual_scale_cues_from_photo_geometry,
)
from brickhouse.survey import ArchitecturalSurvey


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-region-house",
            "name": "Generic region house",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "Canonical front image.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                },
                {
                    "photo_index": 2,
                    "facade": "right",
                    "description": "Right facade image.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                },
            ],
            "known_measurements": [],
            "observations": [
                {
                    "id": "front-boundary",
                    "kind": "building_boundary",
                    "certainty": "certain",
                    "statement": "Front building extent is visible.",
                    "evidence": [
                        {"photo_index": 1, "observation": "Visible front envelope."}
                    ],
                },
                {
                    "id": "front-window",
                    "kind": "opening",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "Front window is visible.",
                    "evidence": [
                        {"photo_index": 1, "observation": "Visible window."}
                    ],
                    "attributes": {"semantic_type": "window"},
                    "attribute_certainty": {"semantic_type": "certain"},
                },
                {
                    "id": "right-window",
                    "kind": "opening",
                    "facade": "right",
                    "certainty": "certain",
                    "statement": "Right window is visible.",
                    "evidence": [
                        {"photo_index": 2, "observation": "Visible right window."}
                    ],
                },
            ],
        }
    )


def _annotation(
    id: str,
    observation_id: str,
    photo_index: int,
    region: tuple[float, float, float, float],
    *,
    source_kind: str = "inferred",
    confidence: float = 0.8,
) -> PhotoGeometryAnnotation:
    x0, y0, x1, y1 = region
    return PhotoGeometryAnnotation.model_validate(
        {
            "id": id,
            "observation_id": observation_id,
            "photo_index": photo_index,
            "region": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
            "source": {"kind": source_kind, "confidence": confidence},
            "statement": f"Geometry annotation {id}.",
        }
    )


def test_width_cue_uses_feature_over_explicit_reference_region_not_full_image() -> None:
    survey = _survey()
    before = deepcopy(survey.model_dump())
    annotations = [
        _annotation("facade-box", "front-boundary", 1, (0.10, 0.10, 0.90, 0.90), confidence=0.9),
        _annotation("window-box", "front-window", 1, (0.30, 0.30, 0.40, 0.65), confidence=0.75),
    ]

    cues = build_visual_scale_cues_from_photo_geometry(
        survey,
        annotations,
        [
            PhotoScaleCueBinding(
                id="front-window-width",
                feature_annotation_id="window-box",
                reference_annotation_id="facade-box",
                axis="width",
                cue_family="window_width",
                prior_id="generic-window-width",
            )
        ],
    )

    assert survey.model_dump() == before
    assert len(cues) == 1
    assert cues[0].normalized_extent == pytest.approx(0.10 / 0.80)
    assert cues[0].confidence == pytest.approx(0.75)
    assert cues[0].photo_index == 1
    assert cues[0].observation_id == "front-window"


def test_height_cue_uses_same_explicit_reference_region() -> None:
    cues = build_visual_scale_cues_from_photo_geometry(
        _survey(),
        [
            _annotation("facade-box", "front-boundary", 1, (0.10, 0.05, 0.90, 0.95)),
            _annotation("window-box", "front-window", 1, (0.30, 0.25, 0.40, 0.55)),
        ],
        [
            PhotoScaleCueBinding(
                id="front-window-height",
                feature_annotation_id="window-box",
                reference_annotation_id="facade-box",
                axis="height",
                cue_family="window_height",
                prior_id="generic-window-height",
            )
        ],
    )

    assert cues[0].normalized_extent == pytest.approx(0.30 / 0.90)


def test_binding_rejects_regions_from_different_photos() -> None:
    annotations = [
        _annotation("front-reference", "front-boundary", 1, (0.10, 0.10, 0.90, 0.90)),
        _annotation("right-feature", "right-window", 2, (0.30, 0.30, 0.40, 0.60)),
    ]

    with pytest.raises(ValueError, match="same photo"):
        build_visual_scale_cues_from_photo_geometry(
            _survey(),
            annotations,
            [
                PhotoScaleCueBinding(
                    id="bad-cross-view-ratio",
                    feature_annotation_id="right-feature",
                    reference_annotation_id="front-reference",
                    axis="width",
                    cue_family="window_width",
                    prior_id="generic-window-width",
                )
            ],
        )


def test_annotation_rejects_unknown_observation_and_unbacked_photo() -> None:
    with pytest.raises(ValueError, match="unknown observation"):
        build_visual_scale_cues_from_photo_geometry(
            _survey(),
            [_annotation("ghost", "missing-opening", 1, (0.1, 0.1, 0.2, 0.2))],
            [],
        )

    with pytest.raises(ValueError, match="not backed"):
        build_visual_scale_cues_from_photo_geometry(
            _survey(),
            [_annotation("wrong-photo", "front-window", 2, (0.1, 0.1, 0.2, 0.2))],
            [],
        )


def test_reference_must_contain_feature_instead_of_inventing_ratio() -> None:
    annotations = [
        _annotation("facade-box", "front-boundary", 1, (0.10, 0.10, 0.60, 0.80)),
        _annotation("window-box", "front-window", 1, (0.55, 0.30, 0.75, 0.60)),
    ]

    with pytest.raises(ValueError, match="contain the feature"):
        build_visual_scale_cues_from_photo_geometry(
            _survey(),
            annotations,
            [
                PhotoScaleCueBinding(
                    id="outside-reference",
                    feature_annotation_id="window-box",
                    reference_annotation_id="facade-box",
                    axis="width",
                    cue_family="window_width",
                    prior_id="generic-window-width",
                )
            ],
        )


def test_generated_default_geometry_is_forbidden() -> None:
    with pytest.raises(ValueError, match="observed or inferred"):
        _annotation(
            "default-box",
            "front-window",
            1,
            (0.2, 0.2, 0.3, 0.4),
            source_kind="generated_default",
        )
