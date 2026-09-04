"""Measure facade rhythm changes introduced only by LEGO window anchoring."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from .window_anchors import AppliedWindowAnchor


class FacadeRhythmFidelity(BaseModel):
    facade: str
    wall_width_studs: int = Field(gt=0)
    opening_ids: tuple[str, ...]
    source_segments_studs: tuple[int, ...]
    anchored_segments_studs: tuple[int, ...]
    max_segment_distortion: float = Field(ge=0)
    mean_segment_distortion: float = Field(ge=0)


Severity = Literal["warning", "blocker"]


def _segments(anchors: list[AppliedWindowAnchor], wall_width: int, *, anchored: bool) -> tuple[int, ...]:
    ordered = sorted(anchors, key=lambda a: ((a.anchored_x_studs if anchored else a.source_x_studs), a.opening_id))
    starts = [a.anchored_x_studs if anchored else a.source_x_studs for a in ordered]
    widths = [a.anchored_width_studs if anchored else a.source_width_studs for a in ordered]
    if not ordered:
        return (wall_width,)
    segments = [starts[0]]
    segments.extend(starts[i] - (starts[i - 1] + widths[i - 1]) for i in range(1, len(ordered)))
    segments.append(wall_width - (starts[-1] + widths[-1]))
    return tuple(segments)


def measure_facade_rhythm(anchors: list[AppliedWindowAnchor], *, wall_width_studs: int) -> FacadeRhythmFidelity | None:
    """Compare edge margins and inter-opening gaps in facade-width units."""
    if wall_width_studs <= 0:
        raise ValueError("wall_width_studs must be positive")
    if not anchors:
        return None
    facades = {anchor.facade.value for anchor in anchors}
    if len(facades) != 1:
        raise ValueError("facade rhythm anchors must belong to one facade")
    source_order = sorted(anchors, key=lambda a: (a.source_x_studs, a.opening_id))
    anchored_order = sorted(anchors, key=lambda a: (a.anchored_x_studs, a.opening_id))
    source_ids = tuple(a.opening_id for a in source_order)
    if source_ids != tuple(a.opening_id for a in anchored_order):
        raise ValueError("LEGO anchoring changed architectural opening order")
    source = _segments(source_order, wall_width_studs, anchored=False)
    represented = _segments(anchored_order, wall_width_studs, anchored=True)
    distortions = tuple(abs(after - before) / wall_width_studs for before, after in zip(source, represented))
    return FacadeRhythmFidelity(facade=next(iter(facades)), wall_width_studs=wall_width_studs, opening_ids=source_ids, source_segments_studs=source, anchored_segments_studs=represented, max_segment_distortion=max(distortions, default=0.0), mean_segment_distortion=sum(distortions) / len(distortions) if distortions else 0.0)


def facade_rhythm_severity(metric: FacadeRhythmFidelity) -> Severity | None:
    if metric.max_segment_distortion >= 0.20 or metric.mean_segment_distortion >= 0.12:
        return "blocker"
    if metric.max_segment_distortion >= 0.10 or metric.mean_segment_distortion >= 0.06:
        return "warning"
    return None
