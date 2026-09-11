import pytest

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.scene.photo_landmarks import (
    LocalLandmarkValidation,
    PhysicalLandmarkIdentityValidation,
    build_architectural_landmark_tracks_from_vision,
    build_relative_landmark_tracks,
)
from brickhouse.scene.photo_rectification import NormalizedImagePoint
from brickhouse.scene.relative_camera_estimation import CalibratedPhotoIntrinsics, estimate_relative_camera_pair
from brickhouse.scene.relative_multiview import reconstruct_relative_landmarks
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.vision.models import (
    VisionArchitecturalLandmarkProposal,
    VisionLandmarkObservationProposal,
    VisionNormalizedImagePoint,
    VisionPhotoEvidenceCandidate,
)


POINTS = [
    (-1.0, -0.8, 4.0), (-0.5, 0.7, 5.0), (0.2, -0.5, 6.0), (0.8, 0.9, 5.5),
    (1.2, -0.2, 7.0), (-0.8, 0.3, 8.0), (0.5, 0.4, 4.5), (1.0, -0.7, 6.5),
    (-0.2, 1.0, 7.5), (1.4, 0.2, 8.5),
]


def _survey(*, second_photo_accepted: bool = True) -> ArchitecturalSurvey:
    evidence = [{"photo_index": 1, "observation": "Element visible in view A."}]
    if second_photo_accepted:
        evidence.append({"photo_index": 2, "observation": "Same element accepted in view B."})
    return ArchitecturalSurvey.model_validate({
        "id": "bh238-generic",
        "name": "BH-238 generic survey",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "View A", "source": {"kind": "observed", "confidence": 1.0}},
            {"photo_index": 2, "facade": "front", "description": "View B", "source": {"kind": "observed", "confidence": 1.0}},
        ],
        "observations": [{
            "id": "architectural-object",
            "kind": "volume",
            "facade": "front",
            "certainty": "certain",
            "statement": "One physical architectural object.",
            "evidence": evidence,
        }],
    })


def _proposal(pid: str, p1=(0.35, 0.4), p2=(0.3, 0.42)) -> VisionArchitecturalLandmarkProposal:
    return VisionArchitecturalLandmarkProposal(
        physical_landmark_id=pid,
        description="Exact upper corner of one physical opening",
        confidence=0.92,
        statement="Provider proposes the same exact architectural corner in both views.",
        observations=[
            VisionLandmarkObservationProposal(
                photo_index=1,
                point=VisionNormalizedImagePoint(x=p1[0], y=p1[1]),
                confidence=0.94,
                survey_observation_id="architectural-object",
                statement="Proposed corner in view A.",
            ),
            VisionLandmarkObservationProposal(
                photo_index=2,
                point=VisionNormalizedImagePoint(x=p2[0], y=p2[1]),
                confidence=0.91,
                survey_observation_id="architectural-object",
                statement="Proposed same physical corner in view B.",
            ),
        ],
    )


def _identity(pid: str, status="CONFIRMED") -> PhysicalLandmarkIdentityValidation:
    return PhysicalLandmarkIdentityValidation(
        physical_landmark_id=pid,
        status=status,
        confidence=0.9,
        source=SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9),
        statement="Cross-view physical identity checked independently of local corner localization.",
    )


def _locals(proposal: VisionArchitecturalLandmarkProposal, *, reject_second=False):
    result = []
    for occurrence in proposal.observations:
        rejected = reject_second and occurrence.photo_index == 2
        result.append(LocalLandmarkValidation(
            physical_landmark_id=proposal.physical_landmark_id,
            photo_index=occurrence.photo_index,
            status="REJECTED" if rejected else "ACCEPTED",
            refined_point=None if rejected else NormalizedImagePoint(x=occurrence.point.x, y=occurrence.point.y),
            repeatability_px=8.0 if rejected else 0.7,
            confidence=0.2 if rejected else 0.95,
            method="bounded seeded corner refinement",
            diagnostic="unstable local corner" if rejected else "stable under bounded seed perturbation",
        ))
    return result


def test_provider_identity_never_becomes_track_without_identity_and_local_validation():
    survey = _survey()
    proposal = _proposal("opening-corner-a")

    assert build_architectural_landmark_tracks_from_vision(survey, [proposal], [], _locals(proposal)) == []
    assert build_architectural_landmark_tracks_from_vision(
        survey, [proposal], [_identity(proposal.physical_landmark_id)], _locals(proposal, reject_second=True)
    ) == []


def test_missing_survey_coverage_stays_explicit_candidate_and_does_not_mutate_survey():
    survey = _survey(second_photo_accepted=False)
    before = survey.model_dump(mode="json")
    proposal = _proposal("opening-corner-b")
    identity = _identity(proposal.physical_landmark_id)
    local = _locals(proposal)

    assert build_architectural_landmark_tracks_from_vision(survey, [proposal], [identity], local) == []

    candidate = VisionPhotoEvidenceCandidate(
        survey_observation_id="architectural-object",
        photo_index=2,
        statement="Provider directly sees the already-known object in this additional photo.",
        confidence=0.88,
        provider="test-provider",
        provider_model="test-model",
    )
    tracks = build_architectural_landmark_tracks_from_vision(
        survey,
        [proposal],
        [identity],
        local,
        photo_evidence_candidates=[candidate],
    )

    assert len(tracks) == 1
    assert tracks[0].status == "CANDIDATE_EVIDENCE"
    assert survey.model_dump(mode="json") == before
    relative = build_relative_landmark_tracks(survey, tracks, photo_evidence_candidates=[candidate])
    assert len(relative) == 1


def _portrait_point(world, camera_x: float, *, width=691, height=1536, focal=900.0):
    x, y, z = world
    cx, cy = width / 2.0, height / 2.0
    u = cx + focal * (x - camera_x) / z
    v = cy - focal * y / z
    return NormalizedImagePoint(x=u / width, y=v / height)


def _relative_track(index: int, world):
    proposal = _proposal(
        f"corner-{index:02d}",
        p1=(_portrait_point(world, 0.0).x, _portrait_point(world, 0.0).y),
        p2=(_portrait_point(world, 1.0).x, _portrait_point(world, 1.0).y),
    )
    architectural = build_architectural_landmark_tracks_from_vision(
        _survey(), [proposal], [_identity(proposal.physical_landmark_id)], _locals(proposal)
    )
    return build_relative_landmark_tracks(_survey(), architectural)[0]


def _pixel_intrinsics(photo_index: int, *, fy=900.0):
    return CalibratedPhotoIntrinsics(
        id=f"portrait-{photo_index}",
        photo_index=photo_index,
        coordinate_space="pixel",
        image_width_px=691,
        image_height_px=1536,
        focal_x_px=900.0,
        focal_y_px=fy,
        principal_x_px=691 / 2.0,
        principal_y_px=1536 / 2.0,
        source=SourceInfo(kind=SourceKind.USER_PROVIDED, confidence=1.0),
        statement="Synthetic pixel calibration for portrait-image regression.",
    )


def test_portrait_pixel_intrinsics_are_converted_to_one_isotropic_bh236_space():
    survey = _survey()
    tracks = [_relative_track(index, world) for index, world in enumerate(POINTS)]
    result = estimate_relative_camera_pair(
        survey,
        [_pixel_intrinsics(1), _pixel_intrinsics(2)],
        tracks,
        first_photo_index=1,
        second_photo_index=2,
    )

    assert result.status == "RESOLVED_RELATIVE"
    assert result.cameras[0].focal_length == pytest.approx(900.0 / 1536.0)
    assert result.cameras[0].principal_x == pytest.approx(0.5)
    assert result.cameras[0].principal_y == pytest.approx(0.5)
    original = tracks[0].observations[0].point
    transformed = result.bh236_tracks[0].observations[0].point
    assert transformed.x == pytest.approx((original.x * 691 + (1536 - 691) / 2) / 1536)
    assert transformed.y == pytest.approx(original.y)

    reconstruction = reconstruct_relative_landmarks(survey, result.cameras, result.bh236_tracks)
    assert reconstruction.status == "RESOLVED_RELATIVE"


def test_non_square_pixel_camera_refuses_material_fx_fy_mismatch_instead_of_distorting():
    survey = _survey()
    tracks = [_relative_track(index, world) for index, world in enumerate(POINTS[:8])]
    result = estimate_relative_camera_pair(
        survey,
        [_pixel_intrinsics(1, fy=760.0), _pixel_intrinsics(2, fy=760.0)],
        tracks,
        first_photo_index=1,
        second_photo_index=2,
    )
    assert result.status == "UNRESOLVED"
    assert result.cameras == []
    assert "fx/fy" in result.diagnostic
