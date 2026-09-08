"""Translate explicit normalized photo geometry into BH-194 visual scale cues.

ArchitecturalSurvey remains immutable semantic evidence. Geometry annotations are a
separate sidecar because a bounding box produced later by a vision model must not
silently become an original Survey observation. Statistical dimension priors remain
separate again in ``scale_estimation``.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey, NormalizedImageRegion

from .scale_estimation import VisualScaleCue


class PhotoGeometryAnnotation(BaseModel):
    """Provenance-bearing image region for one accepted Survey observation."""

    id: str = Field(min_length=1)
    observation_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_geometry_source(self) -> "PhotoGeometryAnnotation":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.INFERRED}:
            raise ValueError("photo geometry source.kind must be observed or inferred")
        return self


class PhotoScaleCueBinding(BaseModel):
    """Explicitly relate one feature box to one reference box on a single image."""

    id: str = Field(min_length=1)
    feature_annotation_id: str = Field(min_length=1)
    reference_annotation_id: str = Field(min_length=1)
    axis: Literal["width", "height"]
    cue_family: str = Field(min_length=1)
    prior_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_distinct_annotations(self) -> "PhotoScaleCueBinding":
        if self.feature_annotation_id == self.reference_annotation_id:
            raise ValueError("feature and reference annotations must be distinct")
        return self


def _axis_bounds(region: NormalizedImageRegion, axis: str) -> tuple[float, float]:
    if axis == "width":
        return region.x0, region.x1
    return region.y0, region.y1


def _axis_extent(region: NormalizedImageRegion, axis: str) -> float:
    low, high = _axis_bounds(region, axis)
    return high - low


def _contains(reference: NormalizedImageRegion, feature: NormalizedImageRegion) -> bool:
    return (
        reference.x0 <= feature.x0
        and reference.y0 <= feature.y0
        and reference.x1 >= feature.x1
        and reference.y1 >= feature.y1
    )


def validate_photo_geometry_annotations(
    survey: ArchitecturalSurvey,
    annotations: list[PhotoGeometryAnnotation],
) -> None:
    """Reject geometry that cannot be traced to accepted Survey evidence."""
    ids = [annotation.id for annotation in annotations]
    if len(ids) != len(set(ids)):
        raise ValueError("photo geometry annotation ids must be unique")

    photo_ids = {photo.photo_index for photo in survey.photos}
    observations = {observation.id: observation for observation in survey.observations}

    for annotation in annotations:
        if annotation.photo_index not in photo_ids:
            raise ValueError(
                f"photo geometry annotation {annotation.id!r} references unknown photo {annotation.photo_index}"
            )
        observation = observations.get(annotation.observation_id)
        if observation is None:
            raise ValueError(
                f"photo geometry annotation {annotation.id!r} references unknown observation {annotation.observation_id!r}"
            )
        evidence_photos = {evidence.photo_index for evidence in observation.evidence}
        if annotation.photo_index not in evidence_photos:
            raise ValueError(
                f"photo geometry annotation {annotation.id!r} is not backed by that observation on photo {annotation.photo_index}"
            )


def build_visual_scale_cues_from_photo_geometry(
    survey: ArchitecturalSurvey,
    annotations: list[PhotoGeometryAnnotation],
    bindings: list[PhotoScaleCueBinding],
) -> list[VisualScaleCue]:
    """Build normalized feature/reference ratios without assuming full-image scale."""
    validate_photo_geometry_annotations(survey, annotations)
    if not bindings:
        return []

    annotation_by_id = {annotation.id: annotation for annotation in annotations}
    binding_ids = [binding.id for binding in bindings]
    if len(binding_ids) != len(set(binding_ids)):
        raise ValueError("photo scale cue binding ids must be unique")

    cues: list[VisualScaleCue] = []
    for binding in bindings:
        feature = annotation_by_id.get(binding.feature_annotation_id)
        reference = annotation_by_id.get(binding.reference_annotation_id)
        if feature is None or reference is None:
            missing = binding.feature_annotation_id if feature is None else binding.reference_annotation_id
            raise ValueError(f"photo scale cue binding {binding.id!r} references unknown annotation {missing!r}")
        if feature.photo_index != reference.photo_index:
            raise ValueError(
                f"photo scale cue binding {binding.id!r} must compare regions from the same photo"
            )
        if not _contains(reference.region, feature.region):
            raise ValueError(
                f"photo scale cue binding {binding.id!r} requires the reference region to contain the feature region"
            )

        feature_extent = _axis_extent(feature.region, binding.axis)
        reference_extent = _axis_extent(reference.region, binding.axis)
        if feature_extent >= reference_extent:
            raise ValueError(
                f"photo scale cue binding {binding.id!r} requires feature extent smaller than reference extent"
            )

        cues.append(
            VisualScaleCue(
                id=binding.id,
                cue_family=binding.cue_family,
                prior_id=binding.prior_id,
                normalized_extent=feature_extent / reference_extent,
                confidence=min(feature.source.confidence, reference.source.confidence),
                photo_index=feature.photo_index,
                observation_id=feature.observation_id,
            )
        )
    return cues
