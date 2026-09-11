"""Explicit architectural landmark correspondences backed by photo/Survey evidence.

This sidecar does not discover or match landmarks. Physical identity is declared
explicitly by the caller or arrives as a separately validated vision proposal.
Accepted Survey evidence remains immutable; an extra directly observed photo may
be carried only as an explicit candidate evidence sidecar.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey

from .photo_rectification import NormalizedImagePoint
from .photo_scale_cues import PhotoGeometryAnnotation, validate_photo_geometry_annotations
from .relative_multiview import RelativeLandmarkObservation, RelativeLandmarkTrack


ArchitecturalLandmarkStatus = Literal["EXPLICIT_MATCH", "VALIDATED_PROPOSAL"]


class CandidatePhotoEvidence(BaseModel):
    """New photo support proposed for an existing Survey observation, never a Survey mutation."""

    id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    physical_landmark_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    point: NormalizedImagePoint
    source: SourceInfo
    statement: str = Field(min_length=1)
    status: Literal["CANDIDATE"] = "CANDIDATE"

    @model_validator(mode="after")
    def validate_source(self) -> "CandidatePhotoEvidence":
        if self.source.kind is not SourceKind.INFERRED:
            raise ValueError("candidate photo evidence must remain inferred until Survey acceptance")
        return self


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
    """Claim that listed 2D observations are the same physical landmark."""

    id: str = Field(min_length=1)
    physical_landmark_id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    observations: list[ArchitecturalLandmarkObservation] = Field(min_length=2)
    status: ArchitecturalLandmarkStatus = "EXPLICIT_MATCH"
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_explicit_identity(self) -> "ArchitecturalLandmarkTrack":
        if self.status == "EXPLICIT_MATCH":
            if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED}:
                raise ValueError("explicit physical landmark identity must be observed or user_provided")
        elif self.source.kind is not SourceKind.INFERRED:
            raise ValueError("validated provider landmark identity must remain inferred")
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("an architectural landmark track may contain at most one observation per photo")
        for item in self.observations:
            if item.physical_landmark_id != self.physical_landmark_id:
                raise ValueError("landmark observation physical identity disagrees with its track identity")
            if item.survey_observation_id != self.survey_observation_id:
                raise ValueError("landmark observation Survey identity disagrees with its track binding")
            if item.coordinate_space_id != "image":
                raise ValueError("BH-237 landmark bridge currently accepts original image coordinates only")
        return self


def validate_architectural_landmark_tracks(
    survey: ArchitecturalSurvey,
    tracks: list[ArchitecturalLandmarkTrack],
    *,
    geometry_annotations: list[PhotoGeometryAnnotation] | None = None,
    evidence_candidates: list[CandidatePhotoEvidence] | None = None,
) -> None:
    """Validate identity, immutable Survey provenance and explicit extra-photo candidates."""
    track_ids = [track.id for track in tracks]
    if len(track_ids) != len(set(track_ids)):
        raise ValueError("architectural landmark track ids must be unique")
    physical_ids = [track.physical_landmark_id for track in tracks]
    if len(physical_ids) != len(set(physical_ids)):
        raise ValueError("physical landmark ids must be unique across tracks")

    known_photos = {photo.photo_index for photo in survey.photos}
    survey_observations = {observation.id: observation for observation in survey.observations}
    annotations = geometry_annotations or []
    if annotations:
        validate_photo_geometry_annotations(survey, annotations)
    annotation_by_id = {annotation.id: annotation for annotation in annotations}

    candidate_by_key: dict[tuple[str, str, int], CandidatePhotoEvidence] = {}
    for candidate in evidence_candidates or []:
        if candidate.photo_index not in known_photos:
            raise ValueError(f"candidate photo evidence {candidate.id!r} references unknown photo {candidate.photo_index}")
        if candidate.survey_observation_id not in survey_observations:
            raise ValueError(f"candidate photo evidence {candidate.id!r} references unknown Survey observation")
        key = (candidate.physical_landmark_id, candidate.survey_observation_id, candidate.photo_index)
        if key in candidate_by_key:
            raise ValueError("candidate photo evidence must be unique per landmark, Survey observation and photo")
        candidate_by_key[key] = candidate

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
                key = (track.physical_landmark_id, track.survey_observation_id, item.photo_index)
                candidate = candidate_by_key.get(key)
                if candidate is None:
                    raise ValueError(
                        f"landmark track {track.id!r} is not backed by accepted Survey evidence or an explicit candidate "
                        f"for observation {track.survey_observation_id!r} on photo {item.photo_index}"
                    )
                if abs(candidate.point.x - item.point.x) > 1e-9 or abs(candidate.point.y - item.point.y) > 1e-9:
                    raise ValueError(f"landmark track {track.id!r} does not preserve its candidate evidence point")
            if item.geometry_annotation_id is None:
                continue
            annotation = annotation_by_id.get(item.geometry_annotation_id)
            if annotation is None:
                raise ValueError(
                    f"landmark track {track.id!r} references unknown photo geometry annotation {item.geometry_annotation_id!r}"
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
    evidence_candidates: list[CandidatePhotoEvidence] | None = None,
) -> list[RelativeLandmarkTrack]:
    """Adapt only validated correspondences to the BH-236 track contract."""
    validate_architectural_landmark_tracks(
        survey,
        tracks,
        geometry_annotations=geometry_annotations,
        evidence_candidates=evidence_candidates,
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
