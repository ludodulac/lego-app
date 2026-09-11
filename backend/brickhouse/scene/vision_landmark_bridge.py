"""Bridge bounded vision landmark proposals into BH-237 architectural tracks.

Provider identity is a proposal, never sufficient on its own. Every accepted track
occurrence must pass bounded local geometry and already be backed by accepted
Survey evidence. When the provider does not know Survey IDs, a point may bind only
through one unambiguous accepted Survey evidence region on that same photo. Extra
photo support omitted by the accepted Survey is preserved as a separate candidate.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.vision.models import VisionLandmarkProposal, VisionLandmarkObservationProposal

from .local_landmark_validation import LocalLandmarkValidation
from .photo_landmarks import (
    ArchitecturalLandmarkObservation,
    ArchitecturalLandmarkTrack,
    CandidatePhotoEvidence,
    validate_architectural_landmark_tracks,
)


class VisionLandmarkBridgeResult(BaseModel):
    tracks: list[ArchitecturalLandmarkTrack] = Field(default_factory=list)
    evidence_candidates: list[CandidatePhotoEvidence] = Field(default_factory=list)
    rejected: dict[str, str] = Field(default_factory=dict)


def _unique_region_binding(
    survey: ArchitecturalSurvey,
    occurrence: VisionLandmarkObservationProposal,
    local: LocalLandmarkValidation,
) -> str | None:
    """Bind only when exactly one accepted Survey region contains the refined point."""
    if occurrence.survey_observation_id is not None:
        return occurrence.survey_observation_id
    if local.refined_point is None:
        return None
    candidates: list[str] = []
    for observation in survey.observations:
        for evidence in observation.evidence:
            if evidence.photo_index != occurrence.photo_index or evidence.region is None:
                continue
            region = evidence.region
            if region.x0 <= local.refined_point.x <= region.x1 and region.y0 <= local.refined_point.y <= region.y1:
                candidates.append(observation.id)
                break
    return candidates[0] if len(candidates) == 1 else None


def bridge_vision_landmarks_to_tracks(
    survey: ArchitecturalSurvey,
    proposals: list[VisionLandmarkProposal],
    local_validations: list[LocalLandmarkValidation],
    *,
    minimum_identity_confidence: float = 0.75,
    minimum_observation_confidence: float = 0.65,
    minimum_candidate_evidence_confidence: float = 0.75,
) -> VisionLandmarkBridgeResult:
    """Accept only traceable, locally stable cross-view proposals without Survey mutation."""
    if not 0 <= minimum_identity_confidence <= 1:
        raise ValueError("minimum_identity_confidence must be in [0,1]")
    validation_by_key: dict[tuple[str, int], LocalLandmarkValidation] = {}
    for validation in local_validations:
        key = (validation.physical_landmark_id, validation.photo_index)
        if key in validation_by_key:
            raise ValueError("local landmark validations must be unique per physical landmark and photo")
        validation_by_key[key] = validation

    known_observations = {item.id: item for item in survey.observations}
    known_photos = {item.photo_index for item in survey.photos}
    tracks: list[ArchitecturalLandmarkTrack] = []
    evidence_candidates: list[CandidatePhotoEvidence] = []
    rejected: dict[str, str] = {}

    for proposal in sorted(proposals, key=lambda item: item.physical_landmark_id):
        landmark_id = proposal.physical_landmark_id
        if proposal.status != "PROPOSED":
            rejected[landmark_id] = proposal.ambiguity_reason or "Provider did not propose this identity as usable."
            continue
        if proposal.identity_confidence < minimum_identity_confidence:
            rejected[landmark_id] = "Provider cross-view physical identity confidence is below the acceptance gate."
            continue

        stable: list[tuple[VisionLandmarkObservationProposal, LocalLandmarkValidation, str | None]] = []
        failure_reason: str | None = None
        for occurrence in sorted(proposal.observations, key=lambda item: item.photo_index):
            if occurrence.status != "PROPOSED" or occurrence.confidence < minimum_observation_confidence:
                continue
            if occurrence.photo_index not in known_photos:
                failure_reason = f"Provider proposal references unknown photo {occurrence.photo_index}."
                break
            local = validation_by_key.get((landmark_id, occurrence.photo_index))
            if local is None or local.status != "ACCEPTED" or local.refined_point is None:
                continue
            bound_id = _unique_region_binding(survey, occurrence, local)
            if bound_id is not None and bound_id not in known_observations:
                failure_reason = f"Provider proposal references unknown Survey observation {bound_id!r}."
                break
            stable.append((occurrence, local, bound_id))
        if failure_reason is not None:
            rejected[landmark_id] = failure_reason
            continue

        direct_ids = {bound_id for _, _, bound_id in stable if bound_id is not None}
        if len(direct_ids) != 1:
            rejected[landmark_id] = (
                "Provider/local evidence does not bind unambiguously to one accepted Survey observation; "
                "visual similarity is not used to choose one."
            )
            continue
        survey_observation_id = next(iter(direct_ids))
        survey_observation = known_observations[survey_observation_id]
        accepted_photos = {item.photo_index for item in survey_observation.evidence}
        accepted: list[ArchitecturalLandmarkObservation] = []

        for occurrence, local, bound_id in stable:
            assert local.refined_point is not None
            source_confidence = min(proposal.identity_confidence, occurrence.confidence)
            if occurrence.photo_index not in accepted_photos:
                if occurrence.confidence >= minimum_candidate_evidence_confidence:
                    evidence_candidates.append(
                        CandidatePhotoEvidence(
                            id=f"candidate-{landmark_id}-photo-{occurrence.photo_index}",
                            survey_observation_id=survey_observation_id,
                            physical_landmark_id=landmark_id,
                            photo_index=occurrence.photo_index,
                            point=local.refined_point,
                            source=SourceInfo(kind=SourceKind.INFERRED, confidence=source_confidence),
                            statement=(
                                "Provider-proposed extra-photo support for the same physical landmark. It remains a new evidence "
                                "candidate and does not modify or impersonate accepted Survey evidence."
                            ),
                        )
                    )
                continue
            if bound_id != survey_observation_id:
                continue
            accepted.append(
                ArchitecturalLandmarkObservation(
                    physical_landmark_id=landmark_id,
                    photo_index=occurrence.photo_index,
                    survey_observation_id=survey_observation_id,
                    point=local.refined_point,
                    source=SourceInfo(kind=SourceKind.INFERRED, confidence=source_confidence),
                    statement=(
                        f"Provider-proposed physical landmark validated by accepted Survey provenance and bounded local geometry. "
                        f"{occurrence.statement} {local.diagnostic}"
                    ),
                )
            )

        if len(accepted) < 2:
            rejected[landmark_id] = (
                "Fewer than two locally stable occurrences with already-accepted Survey photo provenance survived; "
                "extra-photo support remains a separate evidence candidate."
            )
            continue
        tracks.append(
            ArchitecturalLandmarkTrack(
                id=f"vision-track-{landmark_id}",
                physical_landmark_id=landmark_id,
                survey_observation_id=survey_observation_id,
                observations=accepted,
                status="VALIDATED_PROPOSAL",
                source=SourceInfo(kind=SourceKind.INFERRED, confidence=min(item.source.confidence for item in accepted)),
                statement=(
                    f"Vision-proposed physical identity {landmark_id!r} survived accepted Survey provenance and bounded local validation."
                ),
            )
        )

    validate_architectural_landmark_tracks(survey, tracks)
    candidate_keys = [(item.physical_landmark_id, item.survey_observation_id, item.photo_index) for item in evidence_candidates]
    if len(candidate_keys) != len(set(candidate_keys)):
        raise ValueError("vision bridge emitted duplicate candidate photo evidence")
    return VisionLandmarkBridgeResult(
        tracks=tracks,
        evidence_candidates=evidence_candidates,
        rejected=rejected,
    )
