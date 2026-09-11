import json
from pathlib import Path

import pytest

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.scene import (
    ArchitecturalScene,
    NormalizedImagePoint,
    RelativeCameraHypothesis,
    RelativeLandmarkObservation,
    RelativeLandmarkTrack,
    RelativePoint3D,
    RelativeVector3D,
    reconstruct_relative_landmarks,
)
from brickhouse.survey import ArchitecturalSurvey


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "id": "generic-relative-multiview-survey",
        "name": "Generic relative multiview survey",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "Synthetic left camera view",
                "source": {"kind": "observed", "confidence": 1.0},
            },
            {
                "photo_index": 2,
                "facade": "front",
                "description": "Synthetic right camera view",
                "source": {"kind": "observed", "confidence": 1.0},
            },
        ],
        "observations": [
            {
                "id": "target-structure",
                "kind": "volume",
                "facade": "front",
                "certainty": "certain",
                "statement": "The same rigid architectural structure is visible in both synthetic views.",
                "evidence": [
                    {"photo_index": 1, "observation": "Structure visible in left view."},
                    {"photo_index": 2, "observation": "Structure visible in right view."},
                ],
            }
        ],
    })


def _camera(photo_index: int, x: float) -> RelativeCameraHypothesis:
    return RelativeCameraHypothesis(
        id=f"camera-{photo_index}",
        photo_index=photo_index,
        origin=RelativePoint3D(x=x, y=0.0, z=0.0),
        right=RelativeVector3D(x=1.0, y=0.0, z=0.0),
        up=RelativeVector3D(x=0.0, y=1.0, z=0.0),
        forward=RelativeVector3D(x=0.0, y=0.0, z=1.0),
        focal_length=1.0,
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=0.9),
        statement="Synthetic calibrated relative camera hypothesis.",
    )


def _track(track_id: str, point_1: tuple[float, float], point_2: tuple[float, float]) -> RelativeLandmarkTrack:
    return RelativeLandmarkTrack(
        id=track_id,
        observations=[
            RelativeLandmarkObservation(
                photo_index=1,
                observation_id="target-structure",
                point=NormalizedImagePoint(x=point_1[0], y=point_1[1]),
                source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
                statement=f"Explicit synthetic correspondence for {track_id} in photo 1.",
            ),
            RelativeLandmarkObservation(
                photo_index=2,
                observation_id="target-structure",
                point=NormalizedImagePoint(x=point_2[0], y=point_2[1]),
                source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
                statement=f"Explicit synthetic correspondence for {track_id} in photo 2.",
            ),
        ],
    )


def test_sufficient_parallax_recovers_relative_3d_offset_and_reprojection_without_mutation():
    survey = _survey()
    scene_path = Path(__file__).resolve().parents[1] / "fixtures" / "generic_scene_structural_capabilities.json"
    scene = ArchitecturalScene.model_validate(json.loads(scene_path.read_text()))
    survey_before = survey.model_dump(mode="json")
    scene_before = scene.model_dump(mode="json")

    # Camera 2 is one arbitrary relative unit to the right. These observations
    # are exact projections of A=(0,0,4), B=(0.8,0.4,4).
    result = reconstruct_relative_landmarks(
        survey,
        [_camera(1, 0.0), _camera(2, 1.0)],
        [
            _track("A", (0.50, 0.50), (0.25, 0.50)),
            _track("B", (0.70, 0.40), (0.45, 0.40)),
        ],
    )

    assert result.status == "RESOLVED_RELATIVE"
    landmarks = {item.landmark_id: item for item in result.landmarks}
    assert landmarks["A"].status == "RESOLVED_RELATIVE"
    assert landmarks["B"].status == "RESOLVED_RELATIVE"
    assert landmarks["A"].reprojection_rms == pytest.approx(0.0, abs=1e-12)
    assert landmarks["B"].reprojection_rms == pytest.approx(0.0, abs=1e-12)
    assert landmarks["A"].point is not None
    assert landmarks["B"].point is not None
    assert landmarks["B"].point.x - landmarks["A"].point.x == pytest.approx(0.8, abs=1e-9)
    assert landmarks["B"].point.y - landmarks["A"].point.y == pytest.approx(0.4, abs=1e-9)
    assert landmarks["B"].point.z - landmarks["A"].point.z == pytest.approx(0.0, abs=1e-9)

    # The relative sidecar only reads Survey provenance and has no Scene input.
    assert survey.model_dump(mode="json") == survey_before
    assert scene.model_dump(mode="json") == scene_before


def test_zero_baseline_is_unresolved_and_exposes_no_false_3d_point():
    survey = _survey()
    track = _track("degenerate", (0.50, 0.50), (0.50, 0.50))

    result = reconstruct_relative_landmarks(
        survey,
        [_camera(1, 0.0), _camera(2, 0.0)],
        [track],
    )

    assert result.status == "UNRESOLVED"
    assert len(result.landmarks) == 1
    candidate = result.landmarks[0]
    assert candidate.status == "UNRESOLVED"
    assert candidate.point is None
    assert "baseline/parallax" in candidate.diagnostic


def test_relative_reconstruction_is_deterministic():
    survey = _survey()
    cameras = [_camera(1, 0.0), _camera(2, 1.0)]
    tracks = [
        _track("A", (0.50, 0.50), (0.25, 0.50)),
        _track("B", (0.70, 0.40), (0.45, 0.40)),
    ]

    first = reconstruct_relative_landmarks(survey, cameras, tracks)
    second = reconstruct_relative_landmarks(survey, cameras, tracks)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
