from __future__ import annotations

import cv2
import numpy as np

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.scene.local_landmark_validation import LocalLandmarkValidation, validate_local_landmark
from brickhouse.scene.photo_landmarks import build_relative_landmark_tracks
from brickhouse.scene.photo_rectification import NormalizedImagePoint
from brickhouse.scene.relative_camera_estimation import CalibratedPhotoIntrinsics
from brickhouse.scene.relative_multiview import (
    RelativeCameraHypothesis,
    RelativeLandmarkObservation,
    RelativeLandmarkTrack,
    RelativePoint3D,
    RelativeVector3D,
    reconstruct_relative_landmarks,
)
from brickhouse.scene.vision_landmark_bridge import bridge_vision_landmarks_to_tracks
from brickhouse.survey import ArchitecturalSurvey, PhotoEvidence, PhotoView, SurveyObservation
from brickhouse.vision.models import VisionImagePoint, VisionLandmarkObservationProposal, VisionLandmarkProposal


def _source(kind: SourceKind = SourceKind.OBSERVED, confidence: float = 0.95) -> SourceInfo:
    return SourceInfo(kind=kind, confidence=confidence)


def _survey(*, second_photo_is_evidence: bool = True) -> ArchitecturalSurvey:
    evidence = [PhotoEvidence(photo_index=1, observation="Opening corner is visible in photo 1.")]
    if second_photo_is_evidence:
        evidence.append(PhotoEvidence(photo_index=2, observation="Same opening is visible in photo 2."))
    return ArchitecturalSurvey(
        id="generic-bh238-survey",
        name="Generic BH-238 survey",
        photos=[
            PhotoView(
                photo_index=1,
                capture_role="targeted_detail",
                facade=None,
                description="detail A",
                source=_source(),
                image_left_maps_to_facade_offset=None,
            ),
            PhotoView(
                photo_index=2,
                capture_role="targeted_detail",
                facade=None,
                description="detail B",
                source=_source(),
                image_left_maps_to_facade_offset=None,
            ),
        ],
        observations=[
            SurveyObservation(
                id="opening-1",
                kind="opening",
                certainty="certain",
                statement="One physical rectangular opening is visible in the two detail views.",
                evidence=evidence,
            )
        ],
    )


def _proposal(*, status: str = "PROPOSED") -> VisionLandmarkProposal:
    return VisionLandmarkProposal(
        physical_landmark_id="opening-1-top-right",
        description="Exact top-right exterior corner of opening-1 reveal.",
        identity_confidence=0.94,
        status=status,
        ambiguity_reason=None if status == "PROPOSED" else "Repeated nearby edge makes identity ambiguous.",
        observations=[
            VisionLandmarkObservationProposal(
                photo_index=1,
                point=VisionImagePoint(x=0.30, y=0.40),
                survey_observation_id="opening-1",
                survey_object_hint="opening-1 top-right reveal corner",
                confidence=0.93,
                status="PROPOSED",
                statement="Corner is directly visible.",
                provider="generic-test-provider",
            ),
            VisionLandmarkObservationProposal(
                photo_index=2,
                point=VisionImagePoint(x=0.55, y=0.42),
                survey_observation_id="opening-1",
                survey_object_hint="opening-1 top-right reveal corner",
                confidence=0.91,
                status="PROPOSED",
                statement="Same physical reveal corner is directly visible.",
                provider="generic-test-provider",
            ),
        ],
    )


def _local(landmark_id: str, photo_index: int, x: float, y: float) -> LocalLandmarkValidation:
    point = NormalizedImagePoint(x=x, y=y)
    return LocalLandmarkValidation(
        physical_landmark_id=landmark_id,
        photo_index=photo_index,
        status="ACCEPTED",
        proposed_point=point,
        refined_point=point,
        repeatability_rms_px=0.4,
        localization_shift_px=0.7,
        successful_trials=9,
        total_trials=9,
        diagnostic="synthetic stable local corner",
    )


def test_provider_identity_plus_local_validation_builds_bh237_track_without_mutating_survey() -> None:
    survey = _survey()
    before = survey.model_dump_json()
    proposal = _proposal()
    validations = [
        _local(proposal.physical_landmark_id, 1, 0.301, 0.399),
        _local(proposal.physical_landmark_id, 2, 0.551, 0.421),
    ]

    result = bridge_vision_landmarks_to_tracks(survey, [proposal], validations)
    assert len(result.tracks) == 1
    assert result.evidence_candidates == []
    relative = build_relative_landmark_tracks(survey, result.tracks)
    assert len(relative) == 1
    assert [item.photo_index for item in relative[0].observations] == [1, 2]
    assert survey.model_dump_json() == before


def test_ambiguous_identity_is_rejected_even_when_local_points_are_stable() -> None:
    survey = _survey()
    proposal = _proposal(status="AMBIGUOUS")
    validations = [
        _local(proposal.physical_landmark_id, 1, 0.30, 0.40),
        _local(proposal.physical_landmark_id, 2, 0.55, 0.42),
    ]
    result = bridge_vision_landmarks_to_tracks(survey, [proposal], validations)
    assert result.tracks == []
    assert proposal.physical_landmark_id in result.rejected


def test_new_photo_support_stays_candidate_and_does_not_fake_accepted_survey_provenance() -> None:
    survey = _survey(second_photo_is_evidence=False)
    before = survey.model_dump_json()
    proposal = _proposal()
    validations = [
        _local(proposal.physical_landmark_id, 1, 0.30, 0.40),
        _local(proposal.physical_landmark_id, 2, 0.55, 0.42),
    ]
    result = bridge_vision_landmarks_to_tracks(survey, [proposal], validations)
    assert result.tracks == []
    assert len(result.evidence_candidates) == 1
    candidate = result.evidence_candidates[0]
    assert candidate.photo_index == 2
    assert candidate.survey_observation_id == "opening-1"
    assert candidate.status == "CANDIDATE"
    assert survey.model_dump_json() == before


def test_bounded_local_validator_refines_real_corner_and_rejects_flat_patch() -> None:
    image = np.zeros((180, 320), dtype=np.uint8)
    cv2.rectangle(image, (90, 60), (220, 145), 255, 3)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    accepted = validate_local_landmark(
        encoded.tobytes(),
        physical_landmark_id="rectangle-top-left",
        photo_index=1,
        proposed_point=NormalizedImagePoint(x=92 / 320, y=62 / 180),
    )
    assert accepted.status == "ACCEPTED"
    assert accepted.refined_point is not None
    assert accepted.repeatability_rms_px is not None

    flat = np.full((180, 320), 127, dtype=np.uint8)
    ok, flat_encoded = cv2.imencode(".png", flat)
    assert ok
    rejected = validate_local_landmark(
        flat_encoded.tobytes(),
        physical_landmark_id="no-corner",
        photo_index=1,
        proposed_point=NormalizedImagePoint(x=0.5, y=0.5),
    )
    assert rejected.status == "REJECTED"
    assert rejected.refined_point is None


def test_portrait_pixel_intrinsics_preserve_isotropic_physical_focal_without_scalar_normalization_bug() -> None:
    intrinsics = CalibratedPhotoIntrinsics.from_pixel_intrinsics(
        id="portrait-camera",
        photo_index=1,
        image_width_px=100,
        image_height_px=200,
        focal_x_px=100.0,
        focal_y_px=100.0,
        principal_x_px=50.0,
        principal_y_px=100.0,
        source=_source(SourceKind.USER_PROVIDED),
        statement="Synthetic calibrated portrait camera.",
    )
    assert intrinsics.focal_x == 1.0
    assert intrinsics.focal_y == 0.5
    assert intrinsics.focal_x != intrinsics.focal_y

    survey = _survey()
    cameras = [
        RelativeCameraHypothesis(
            id="c1", photo_index=1,
            origin=RelativePoint3D(x=0, y=0, z=0),
            right=RelativeVector3D(x=1, y=0, z=0), up=RelativeVector3D(x=0, y=1, z=0), forward=RelativeVector3D(x=0, y=0, z=1),
            focal_x=1.0, focal_y=0.5, principal_x=0.5, principal_y=0.5,
            source=_source(SourceKind.INFERRED), statement="synthetic portrait camera 1",
        ),
        RelativeCameraHypothesis(
            id="c2", photo_index=2,
            origin=RelativePoint3D(x=1, y=0, z=0),
            right=RelativeVector3D(x=1, y=0, z=0), up=RelativeVector3D(x=0, y=1, z=0), forward=RelativeVector3D(x=0, y=0, z=1),
            focal_x=1.0, focal_y=0.5, principal_x=0.5, principal_y=0.5,
            source=_source(SourceKind.INFERRED), statement="synthetic portrait camera 2",
        ),
    ]
    track = RelativeLandmarkTrack(
        id="portrait-point",
        observations=[
            RelativeLandmarkObservation(
                photo_index=1, observation_id="opening-1", point=NormalizedImagePoint(x=0.60, y=0.4625),
                source=_source(), statement="synthetic projection 1",
            ),
            RelativeLandmarkObservation(
                photo_index=2, observation_id="opening-1", point=NormalizedImagePoint(x=0.35, y=0.4625),
                source=_source(), statement="synthetic projection 2",
            ),
        ],
    )
    result = reconstruct_relative_landmarks(survey, cameras, [track], maximum_reprojection_rms=1e-8)
    assert result.status == "RESOLVED_RELATIVE"
    candidate = result.landmarks[0]
    assert candidate.status == "RESOLVED_RELATIVE"
    assert candidate.reprojection_rms is not None and candidate.reprojection_rms < 1e-8
