import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, NormalizedImagePoint, reconstruct_relative_landmarks
from brickhouse.scene.photo_landmarks import (
    ArchitecturalLandmarkObservation,
    ArchitecturalLandmarkTrack,
    build_relative_landmark_tracks,
)
from brickhouse.scene.photo_scale_cues import PhotoGeometryAnnotation
from brickhouse.scene.relative_camera_estimation import (
    CalibratedPhotoIntrinsics,
    estimate_relative_camera_pair,
)
from brickhouse.survey import ArchitecturalSurvey, NormalizedImageRegion


POINTS = [
    (-1.0, -0.8, 4.0),
    (-0.5, 0.7, 5.0),
    (0.2, -0.5, 6.0),
    (0.8, 0.9, 5.5),
    (1.2, -0.2, 7.0),
    (-0.8, 0.3, 8.0),
    (0.5, 0.4, 4.5),
    (1.0, -0.7, 6.5),
    (-0.2, 1.0, 7.5),
    (1.4, 0.2, 8.5),
    (0.1, -0.9, 5.8),
    (0.9, 0.6, 7.2),
]
FOCAL = 0.8


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "id": "generic-photo-landmark-bridge",
        "name": "Generic photo landmark bridge",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "Synthetic view A", "source": {"kind": "observed", "confidence": 1.0}},
            {"photo_index": 2, "facade": "front", "description": "Synthetic view B", "source": {"kind": "observed", "confidence": 1.0}},
        ],
        "observations": [{
            "id": "rigid-architecture",
            "kind": "volume",
            "facade": "front",
            "certainty": "certain",
            "statement": "One rigid architectural element is explicitly identified in both views.",
            "evidence": [
                {"photo_index": 1, "observation": "Rigid element visible in view A."},
                {"photo_index": 2, "observation": "The same rigid element is explicitly identified in view B."},
            ],
        }],
    })


def _image_point(world, camera_x: float) -> NormalizedImagePoint:
    x, y, z = world
    return NormalizedImagePoint(
        x=0.5 + FOCAL * (x - camera_x) / z,
        y=0.5 - FOCAL * y / z,
    )


def _explicit_track(index: int, world) -> ArchitecturalLandmarkTrack:
    physical_id = f"corner-{index:02d}"
    return ArchitecturalLandmarkTrack(
        id=f"track-{index:02d}",
        physical_landmark_id=physical_id,
        survey_observation_id="rigid-architecture",
        source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
        statement=f"Explicit physical identity for architectural corner {index}.",
        observations=[
            ArchitecturalLandmarkObservation(
                physical_landmark_id=physical_id,
                photo_index=1,
                survey_observation_id="rigid-architecture",
                point=_image_point(world, 0.0),
                source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
                statement="Explicit point observation in view A.",
            ),
            ArchitecturalLandmarkObservation(
                physical_landmark_id=physical_id,
                photo_index=2,
                survey_observation_id="rigid-architecture",
                point=_image_point(world, 1.0),
                source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
                statement="Explicit point observation in view B.",
            ),
        ],
    )


def _intrinsics(photo_index: int) -> CalibratedPhotoIntrinsics:
    return CalibratedPhotoIntrinsics(
        id=f"intrinsics-{photo_index}",
        photo_index=photo_index,
        focal_length=FOCAL,
        principal_x=0.5,
        principal_y=0.5,
        source=SourceInfo(kind=SourceKind.USER_PROVIDED, confidence=1.0),
        statement="Synthetic fixed calibrated intrinsics; not estimated from correspondences.",
    )


def test_explicit_landmarks_validate_existing_photo_geometry_and_convert_to_bh236_tracks():
    survey = _survey()
    track = _explicit_track(0, POINTS[0])
    observations = []
    annotations = []
    for item in track.observations:
        annotation_id = f"region-{item.photo_index}"
        observations.append(item.model_copy(update={"geometry_annotation_id": annotation_id}))
        annotations.append(PhotoGeometryAnnotation(
            id=annotation_id,
            observation_id="rigid-architecture",
            photo_index=item.photo_index,
            region=NormalizedImageRegion(
                x0=max(0.0, item.point.x - 0.02),
                y0=max(0.0, item.point.y - 0.02),
                x1=min(1.0, item.point.x + 0.02),
                y1=min(1.0, item.point.y + 0.02),
            ),
            source=SourceInfo(kind=SourceKind.INFERRED, confidence=0.9),
            statement="Existing geometry sidecar region containing the explicit landmark.",
        ))
    track = track.model_copy(update={"observations": observations})

    relative = build_relative_landmark_tracks(survey, [track], geometry_annotations=annotations)

    assert len(relative) == 1
    assert relative[0].id == "corner-00"
    assert [item.photo_index for item in relative[0].observations] == [1, 2]
    assert all(item.observation_id == "rigid-architecture" for item in relative[0].observations)


def test_inconsistent_physical_identity_and_invalid_survey_provenance_are_rejected():
    valid = _explicit_track(0, POINTS[0])
    bad_identity = valid.observations[1].model_copy(update={"physical_landmark_id": "different-corner"})
    with pytest.raises(ValidationError, match="physical identity disagrees"):
        ArchitecturalLandmarkTrack.model_validate(valid.model_dump() | {"observations": [valid.observations[0].model_dump(), bad_identity.model_dump()]})

    survey = _survey()
    bad_provenance = _explicit_track(1, POINTS[1])
    changed = bad_provenance.observations[1].model_copy(update={"survey_observation_id": "missing-observation"})
    with pytest.raises(ValidationError, match="Survey identity disagrees"):
        bad_provenance.model_copy(update={"observations": [bad_provenance.observations[0], changed]}).model_validate(
            bad_provenance.model_dump() | {"observations": [bad_provenance.observations[0].model_dump(), changed.model_dump()]}
        )


def test_calibrated_explicit_tracks_resolve_camera_then_bh236_without_mutation_and_deterministically():
    survey = _survey()
    scene_path = Path(__file__).resolve().parents[1] / "fixtures" / "generic_scene_structural_capabilities.json"
    scene = ArchitecturalScene.model_validate(json.loads(scene_path.read_text()))
    survey_before = survey.model_dump(mode="json")
    scene_before = scene.model_dump(mode="json")
    explicit = [_explicit_track(index, point) for index, point in enumerate(POINTS)]
    tracks = build_relative_landmark_tracks(survey, explicit)
    intrinsics = [_intrinsics(1), _intrinsics(2)]

    first_camera = estimate_relative_camera_pair(
        survey,
        intrinsics,
        tracks,
        first_photo_index=1,
        second_photo_index=2,
    )
    second_camera = estimate_relative_camera_pair(
        survey,
        intrinsics,
        tracks,
        first_photo_index=1,
        second_photo_index=2,
    )

    assert first_camera.status == "RESOLVED_RELATIVE"
    assert first_camera.model_dump(mode="json") == second_camera.model_dump(mode="json")
    assert first_camera.positive_depth_fraction == pytest.approx(1.0)
    assert first_camera.median_parallax_degrees is not None and first_camera.median_parallax_degrees > 1.0
    reconstruction = reconstruct_relative_landmarks(survey, first_camera.cameras, tracks)
    assert reconstruction.status == "RESOLVED_RELATIVE"
    assert all(item.status == "RESOLVED_RELATIVE" for item in reconstruction.landmarks)
    assert survey.model_dump(mode="json") == survey_before
    assert scene.model_dump(mode="json") == scene_before


def test_degenerate_correspondences_and_missing_intrinsics_are_unresolved_without_false_camera():
    survey = _survey()
    repeated = NormalizedImagePoint(x=0.5, y=0.5)
    tracks = []
    for index in range(8):
        track = _explicit_track(index, POINTS[index])
        rewritten = [item.model_copy(update={"point": repeated}) for item in track.observations]
        tracks.append(track.model_copy(update={"observations": rewritten}))
    relative = build_relative_landmark_tracks(survey, tracks)

    degenerate = estimate_relative_camera_pair(
        survey,
        [_intrinsics(1), _intrinsics(2)],
        relative,
        first_photo_index=1,
        second_photo_index=2,
    )
    missing_intrinsics = estimate_relative_camera_pair(
        survey,
        [_intrinsics(1)],
        relative,
        first_photo_index=1,
        second_photo_index=2,
    )

    assert degenerate.status == "UNRESOLVED"
    assert degenerate.cameras == []
    assert "degenerate" in degenerate.diagnostic.lower()
    assert missing_intrinsics.status == "UNRESOLVED"
    assert missing_intrinsics.cameras == []
    assert "intrinsics" in missing_intrinsics.diagnostic.lower()
