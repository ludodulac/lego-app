"""Explicit architectural landmark correspondences backed by photo/Survey evidence.

BH-237 consumes explicit tracks; BH-238 adds the narrow boundary that can accept a
vision-provider proposal only after physical identity, Survey provenance and local
localization have each been validated. The provider never creates geometric truth,
and candidate extra photo evidence never mutates the accepted Survey.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.vision.models import VisionArchitecturalLandmarkProposal, VisionPhotoEvidenceCandidate

from .photo_rectification import NormalizedImagePoint
from .photo_scale_cues import PhotoGeometryAnnotation, validate_photo_geometry_annotations
from .relative_multiview import RelativeLandmarkObservation, RelativeLandmarkTrack


ArchitecturalLandmarkStatus = Literal["EXPLICIT_MATCH", "CANDIDATE_EVIDENCE"]


class ArchitecturalLandmarkObservation(BaseModel):
    """One explicitly identified occurrence of a physical landmark in one photo."""

    physical_landmark_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    survey_observation_id: str = Field(min_length=1)
    point: NormalizedImagePoint
    source: SourceInfo
    statement: str = Field(min_length=1)
    coordinate_space_id: str = Field(default="image", min_length=1)
    geometry_annotation_id: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "ArchitecturalLandmarkObservation":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.INFERRED}:
            raise ValueError("architectural landmark observation source must be observed or inferred")
        return self


class ArchitecturalLandmarkTrack(BaseModel):
    """Explicit claim that listed 2D observations are the same physical landmark."""

    id: str = Field(min_length=1)
    physical_landmark_id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    observations: list[ArchitecturalLandmarkObservation] = Field(min_length=2)
    status: ArchitecturalLandmarkStatus = "EXPLICIT_MATCH"
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_explicit_identity(self) -> "ArchitecturalLandmarkTrack":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED}:
            raise ValueError("physical landmark identity must be explicitly observed or user_provided")
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("an architectural landmark track may contain at most one observation per photo")
        for item in self.observations:
            if item.physical_landmark_id != self.physical_landmark_id:
                raise ValueError("landmark observation physical identity disagrees with its explicit track identity")
            if item.survey_observation_id != self.survey_observation_id:
                raise ValueError("landmark observation Survey identity disagrees with its explicit track binding")
            if item.coordinate_space_id != "image":
                raise ValueError("BH-237 landmark bridge currently accepts original image coordinates only")
        return self


class LocalLandmarkValidation(BaseModel):
    """Bounded local localization verdict for one provider-proposed occurrence.

    The validator receives the provider's physical_landmark_id; it may refine or
    reject the point but is deliberately unable to invent or change that identity.
    """

    physical_landmark_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    status: Literal["ACCEPTED", "AMBIGUOUS", "REJECTED"]
    refined_point: NormalizedImagePoint | None = None
    repeatability_px: float | None = Field(default=None, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    method: str = Field(min_length=1)
    diagnostic: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_local_result(self) -> "LocalLandmarkValidation":
        if self.status == "ACCEPTED" and self.refined_point is None:
            raise ValueError("accepted local landmark validation requires a refined point")
        if self.status != "ACCEPTED" and self.refined_point is not None:
            raise ValueError("ambiguous or rejected local landmark validation must not expose a refined point")
        return self


class PhysicalLandmarkIdentityValidation(BaseModel):
    """Independent acceptance/rejection of a provider's cross-view identity claim."""

    physical_landmark_id: str = Field(min_length=1)
    status: Literal["CONFIRMED", "AMBIGUOUS", "REJECTED"]
    confidence: float = Field(ge=0.0, le=1.0)
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> "PhysicalLandmarkIdentityValidation":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED}:
            raise ValueError("physical identity confirmation must be directly observed or user_provided")
        return self


class PhysicalLandmarkSurveyBinding(BaseModel):
    """Explicit later binding from a provider landmark to one accepted Survey observation.

    The normal analyze-photos request precedes or is independent of an accepted Survey,
    so the provider is not required to know Survey IDs. This sidecar supplies that
    provenance later without guessing or mutating either the provider proposal or Survey.
    """

    physical_landmark_id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> "PhysicalLandmarkSurveyBinding":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED}:
            raise ValueError("landmark-to-Survey binding must be directly observed or user_provided")
        return self


def _candidate_evidence_keys(candidates: list[VisionPhotoEvidenceCandidate]) -> set[tuple[str, int]]:
    return {
        (candidate.survey_observation_id, candidate.photo_index)
        for candidate in candidates
        if candidate.status == "PROPOSED"
    }


def build_architectural_landmark_tracks_from_vision(
    survey: ArchitecturalSurvey,
    proposals: list[VisionArchitecturalLandmarkProposal],
    identity_validations: list[PhysicalLandmarkIdentityValidation],
    local_validations: list[LocalLandmarkValidation],
    *,
    survey_bindings: list[PhysicalLandmarkSurveyBinding] | None = None,
    photo_evidence_candidates: list[VisionPhotoEvidenceCandidate] | None = None,
) -> list[ArchitecturalLandmarkTrack]:
    """Promote only fully validated provider proposals into BH-237 track inputs.

    Candidate photo evidence may close a coverage omission for BH-237 while staying
    explicitly marked CANDIDATE_EVIDENCE. It never changes ``survey`` and is not
    silently treated as accepted Survey evidence. When analyze-photos had no Survey
    context, an explicit later ``survey_bindings`` entry supplies the required link.
    """
    identity_by_id = {item.physical_landmark_id: item for item in identity_validations}
    if len(identity_by_id) != len(identity_validations):
        raise ValueError("physical landmark identity validations must be unique")
    local_by_key = {(item.physical_landmark_id, item.photo_index): item for item in local_validations}
    if len(local_by_key) != len(local_validations):
        raise ValueError("local landmark validations must be unique per physical landmark and photo")
    binding_by_id = {item.physical_landmark_id: item for item in (survey_bindings or [])}
    if len(binding_by_id) != len(survey_bindings or []):
        raise ValueError("landmark-to-Survey bindings must be unique per physical landmark")

    known_photos = {photo.photo_index for photo in survey.photos}
    survey_observations = {observation.id: observation for observation in survey.observations}
    candidate_keys = _candidate_evidence_keys(photo_evidence_candidates or [])
    tracks: list[ArchitecturalLandmarkTrack] = []

    for proposal in sorted(proposals, key=lambda item: item.physical_landmark_id):
        if proposal.identity_status != "PROPOSED":
            continue
        identity = identity_by_id.get(proposal.physical_landmark_id)
        if identity is None or identity.status != "CONFIRMED":
            continue

        proposed_survey_ids = {
            occurrence.survey_observation_id
            for occurrence in proposal.observations
            if occurrence.survey_observation_id
        }
        if len(proposed_survey_ids) > 1:
            continue
        proposed_survey_id = next(iter(proposed_survey_ids)) if proposed_survey_ids else None
        binding = binding_by_id.get(proposal.physical_landmark_id)
        if binding is not None and proposed_survey_id is not None and binding.survey_observation_id != proposed_survey_id:
            continue
        survey_observation_id = proposed_survey_id or (binding.survey_observation_id if binding is not None else None)
        if survey_observation_id is None:
            continue
        survey_observation = survey_observations.get(survey_observation_id)
        if survey_observation is None:
            continue
        accepted_evidence_photos = {evidence.photo_index for evidence in survey_observation.evidence}

        observations: list[ArchitecturalLandmarkObservation] = []
        used_candidate_evidence = False
        failed = False
        for occurrence in sorted(proposal.observations, key=lambda item: item.photo_index):
            if occurrence.status != "PROPOSED" or occurrence.photo_index not in known_photos:
                failed = True
                break
            if occurrence.survey_observation_id not in {None, survey_observation_id}:
                failed = True
                break
            local = local_by_key.get((proposal.physical_landmark_id, occurrence.photo_index))
            if local is None or local.status != "ACCEPTED" or local.refined_point is None:
                failed = True
                break
            if occurrence.photo_index not in accepted_evidence_photos:
                if (survey_observation_id, occurrence.photo_index) not in candidate_keys:
                    failed = True
                    break
                used_candidate_evidence = True
            observations.append(
                ArchitecturalLandmarkObservation(
                    physical_landmark_id=proposal.physical_landmark_id,
                    photo_index=occurrence.photo_index,
                    survey_observation_id=survey_observation_id,
                    point=local.refined_point,
                    source=SourceInfo(
                        kind=SourceKind.OBSERVED,
                        confidence=min(occurrence.confidence, local.confidence, identity.confidence),
                    ),
                    statement=f"{occurrence.statement} Local validation: {local.diagnostic}",
                )
            )
        if failed or len(observations) < 2:
            continue
        binding_statement = f" Survey binding: {binding.statement}" if binding is not None else ""
        tracks.append(
            ArchitecturalLandmarkTrack(
                id=f"vision-track-{proposal.physical_landmark_id}",
                physical_landmark_id=proposal.physical_landmark_id,
                survey_observation_id=survey_observation_id,
                observations=observations,
                status="CANDIDATE_EVIDENCE" if used_candidate_evidence else "EXPLICIT_MATCH",
                source=SourceInfo(kind=SourceKind.OBSERVED, confidence=min(item.source.confidence for item in observations)),
                statement=(
                    f"Validated provider proposal: {proposal.description}. {identity.statement}{binding_statement}"
                    + (" Includes separately recorded candidate photo evidence; accepted Survey is unchanged." if used_candidate_evidence else "")
                ),
            )
        )
    return tracks


def validate_architectural_landmark_tracks(
    survey: ArchitecturalSurvey,
    tracks: list[ArchitecturalLandmarkTrack],
    *,
    geometry_annotations: list[PhotoGeometryAnnotation] | None = None,
    photo_evidence_candidates: list[VisionPhotoEvidenceCandidate] | None = None,
) -> None:
    """Validate explicit identity, photo provenance and optional existing geometry sidecars."""
    track_ids = [track.id for track in tracks]
    if len(track_ids) != len(set(track_ids)):
        raise ValueError("architectural landmark track ids must be unique")
    physical_ids = [track.physical_landmark_id for track in tracks]
    if len(physical_ids) != len(set(physical_ids)):
        raise ValueError("physical landmark ids must be unique across explicit tracks")

    known_photos = {photo.photo_index for photo in survey.photos}
    survey_observations = {observation.id: observation for observation in survey.observations}
    candidate_keys = _candidate_evidence_keys(photo_evidence_candidates or [])
    annotations = geometry_annotations or []
    if annotations:
        validate_photo_geometry_annotations(survey, annotations)
    annotation_by_id = {annotation.id: annotation for annotation in annotations}

    for track in tracks:
        observation = survey_observations.get(track.survey_observation_id)
        if observation is None:
            raise ValueError(
                f"landmark track {track.id!r} references unknown Survey observation {track.survey_observation_id!r}"
            )
        evidence_photos = {evidence.photo_index for evidence in observation.evidence}
        for item in track.observations:
            if item.photo_index not in known_photos:
                raise ValueError(f"landmark track {track.id!r} references unknown photo {item.photo_index}")
            if item.photo_index not in evidence_photos:
                if track.status != "CANDIDATE_EVIDENCE" or (track.survey_observation_id, item.photo_index) not in candidate_keys:
                    raise ValueError(
                        f"landmark track {track.id!r} is not backed by accepted Survey evidence or an explicit candidate "
                        f"for observation {track.survey_observation_id!r} on photo {item.photo_index}"
                    )
            if item.geometry_annotation_id is None:
                continue
            annotation = annotation_by_id.get(item.geometry_annotation_id)
            if annotation is None:
                raise ValueError(
                    f"landmark track {track.id!r} references unknown photo geometry annotation "
                    f"{item.geometry_annotation_id!r}"
                )
            if (
                annotation.photo_index != item.photo_index
                or annotation.observation_id != item.survey_observation_id
                or annotation.coordinate_space_id != item.coordinate_space_id
            ):
                raise ValueError(
                    f"landmark track {track.id!r} geometry annotation does not share its photo, Survey identity and coordinate space"
                )
            region = annotation.region
            if not (region.x0 <= item.point.x <= region.x1 and region.y0 <= item.point.y <= region.y1):
                raise ValueError(
                    f"landmark track {track.id!r} point lies outside geometry annotation {annotation.id!r}"
                )


def build_relative_landmark_tracks(
    survey: ArchitecturalSurvey,
    tracks: list[ArchitecturalLandmarkTrack],
    *,
    geometry_annotations: list[PhotoGeometryAnnotation] | None = None,
    photo_evidence_candidates: list[VisionPhotoEvidenceCandidate] | None = None,
) -> list[RelativeLandmarkTrack]:
    """Adapt only validated explicit/candidate-provenance correspondences to BH-236 tracks."""
    validate_architectural_landmark_tracks(
        survey,
        tracks,
        geometry_annotations=geometry_annotations,
        photo_evidence_candidates=photo_evidence_candidates,
    )
    result: list[RelativeLandmarkTrack] = []
    for track in sorted(tracks, key=lambda item: item.physical_landmark_id):
        result.append(
            RelativeLandmarkTrack(
                id=track.physical_landmark_id,
                observations=[
                    RelativeLandmarkObservation(
                        photo_index=item.photo_index,
                        observation_id=item.survey_observation_id,
                        point=item.point,
                        source=item.source,
                        statement=item.statement,
                    )
                    for item in sorted(track.observations, key=lambda value: value.photo_index)
                ],
            )
        )
    return result
