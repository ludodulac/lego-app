import pytest

from brickhouse.scene.photo_rectification import (
    NormalizedImagePoint,
    PlanarPhotoRectification,
    rectified_plane_reference_annotation,
    rectify_photo_geometry_annotation,
    rectify_point,
)
from brickhouse.scene.photo_scale_cues import (
    PhotoGeometryAnnotation,
    PhotoScaleCueBinding,
    build_visual_scale_cues_from_photo_geometry,
)
from brickhouse.survey import ArchitecturalSurvey


def _rectification(confidence: float = 0.72) -> PlanarPhotoRectification:
    return PlanarPhotoRectification.model_validate(
        {
            "id": "right-wall-rectified",
            "photo_index": 1,
            "source_quad": {
                "top_left": {"x": 0.10, "y": 0.10},
                "top_right": {"x": 0.90, "y": 0.10},
                "bottom_right": {"x": 0.80, "y": 0.90},
                "bottom_left": {"x": 0.20, "y": 0.90},
            },
            "source": {"kind": "inferred", "confidence": confidence},
            "statement": "Plane corners inferred from two horizontal and two vertical facade boundaries.",
        }
    )


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-oblique-house",
            "name": "Generic oblique house",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "right",
                    "description": "Oblique facade view.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                },
                {
                    "photo_index": 2,
                    "facade": "front",
                    "description": "Canonical front context view.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                },
            ],
            "known_measurements": [],
            "observations": [
                {
                    "id": "wall",
                    "kind": "building_boundary",
                    "certainty": "certain",
                    "statement": "Wall plane visible.",
                    "evidence": [{"photo_index": 1, "observation": "Visible wall plane."}],
                },
                {
                    "id": "window",
                    "kind": "opening",
                    "facade": "right",
                    "certainty": "certain",
                    "statement": "Window visible.",
                    "evidence": [{"photo_index": 1, "observation": "Visible opening."}],
                },
            ],
        }
    )


def _feature(confidence: float = 0.84) -> PhotoGeometryAnnotation:
    return PhotoGeometryAnnotation.model_validate(
        {
            "id": "window-image-box",
            "observation_id": "window",
            "photo_index": 1,
            "region": {"x0": 0.42, "y0": 0.30, "x1": 0.58, "y1": 0.70},
            "source": {"kind": "inferred", "confidence": confidence},
            "statement": "Original-image opening bounds.",
        }
    )


def test_trapezoid_corners_map_to_unit_rectangle() -> None:
    rectification = _rectification()
    source = rectification.source_quad
    expected = [
        (source.top_left, (0.0, 0.0)),
        (source.top_right, (1.0, 0.0)),
        (source.bottom_right, (1.0, 1.0)),
        (source.bottom_left, (0.0, 1.0)),
    ]

    for point, (x, y) in expected:
        mapped = rectify_point(rectification, point)
        assert mapped.x == pytest.approx(x, abs=1e-8)
        assert mapped.y == pytest.approx(y, abs=1e-8)


def test_rectified_feature_ratio_uses_plane_space_not_raw_image_width() -> None:
    rectification = _rectification()
    rectified = rectify_photo_geometry_annotation(rectification, _feature())
    reference = rectified_plane_reference_annotation(
        rectification,
        annotation_id="right-wall-reference",
        observation_id="wall",
        statement="Rectified wall plane reference.",
    )

    cues = build_visual_scale_cues_from_photo_geometry(
        _survey(),
        [rectified, reference],
        [
            PhotoScaleCueBinding(
                id="rectified-window-width",
                feature_annotation_id=rectified.id,
                reference_annotation_id=reference.id,
                axis="width",
                cue_family="window_width",
                prior_id="window-prior",
            )
        ],
    )

    # Raw image width is 0.16. Perspective rectification correctly changes the
    # plane-space extent for this synthetic trapezoid to about 0.24615.
    assert cues[0].normalized_extent == pytest.approx(0.246153846, rel=1e-6)
    assert cues[0].normalized_extent != pytest.approx(0.16)
    assert rectified.coordinate_space_id == rectification.id


def test_rectification_confidence_caps_derived_geometry_confidence() -> None:
    rectified = rectify_photo_geometry_annotation(_rectification(confidence=0.61), _feature(confidence=0.90))

    assert rectified.source.kind.value == "inferred"
    assert rectified.source.confidence == pytest.approx(0.61)


def test_cross_coordinate_space_binding_is_rejected() -> None:
    rectification = _rectification()
    rectified = rectify_photo_geometry_annotation(rectification, _feature())
    original_reference = PhotoGeometryAnnotation.model_validate(
        {
            "id": "wall-image-reference",
            "observation_id": "wall",
            "photo_index": 1,
            "region": {"x0": 0.10, "y0": 0.10, "x1": 0.90, "y1": 0.90},
            "source": {"kind": "inferred", "confidence": 0.8},
            "statement": "Original image reference bounds.",
        }
    )

    with pytest.raises(ValueError, match="same coordinate space"):
        build_visual_scale_cues_from_photo_geometry(
            _survey(),
            [rectified, original_reference],
            [
                PhotoScaleCueBinding(
                    id="mixed-space",
                    feature_annotation_id=rectified.id,
                    reference_annotation_id=original_reference.id,
                    axis="width",
                    cue_family="window_width",
                    prior_id="window-prior",
                )
            ],
        )


def test_degenerate_or_self_crossing_quad_is_rejected() -> None:
    with pytest.raises(ValueError, match="convex|non-degenerate"):
        PlanarPhotoRectification.model_validate(
            {
                "id": "bad-plane",
                "photo_index": 1,
                "source_quad": {
                    "top_left": {"x": 0.1, "y": 0.1},
                    "top_right": {"x": 0.9, "y": 0.9},
                    "bottom_right": {"x": 0.9, "y": 0.1},
                    "bottom_left": {"x": 0.1, "y": 0.9},
                },
                "source": {"kind": "inferred", "confidence": 0.7},
                "statement": "Invalid crossing plane.",
            }
        )


def test_feature_outside_rectified_plane_is_rejected_without_extrapolation() -> None:
    payload = _feature().model_dump()
    payload["region"] = {"x0": 0.05, "y0": 0.30, "x1": 0.15, "y1": 0.60}
    outside = PhotoGeometryAnnotation.model_validate(payload)

    with pytest.raises(ValueError, match="outside the rectification source plane"):
        rectify_photo_geometry_annotation(_rectification(), outside)
