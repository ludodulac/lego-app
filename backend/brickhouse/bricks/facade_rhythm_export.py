"""Export-facing facade-rhythm fidelity diagnostics.

This boundary keeps the architectural metric independent from the export schema
while making the recognition constraint consumable by the pipeline.
"""
from __future__ import annotations

from collections import defaultdict

from .export import BrickExportFidelityIssue
from .facade_rhythm_fidelity import facade_rhythm_severity, measure_facade_rhythm


def facade_rhythm_fidelity_issues(application) -> list[BrickExportFidelityIssue]:
    """Return one traceable issue for every materially distorted facade rhythm."""
    anchors_by_facade = defaultdict(list)
    for anchor in application.anchors:
        anchors_by_facade[anchor.facade].append(anchor)

    wall_widths = {
        wall.facade: wall.grid.width_studs
        for wall in application.shell.walls
    }
    issues: list[BrickExportFidelityIssue] = []
    for facade in sorted(anchors_by_facade, key=lambda item: item.value):
        wall_width = wall_widths.get(facade)
        if wall_width is None:
            continue
        metric = measure_facade_rhythm(
            anchors_by_facade[facade],
            wall_width_studs=wall_width,
        )
        if metric is None:
            continue
        severity = facade_rhythm_severity(metric)
        if severity is None:
            continue
        opening_ids = ", ".join(metric.opening_ids)
        issues.append(BrickExportFidelityIssue(
            code="lego_facade_rhythm_distortion",
            severity=severity,
            object_id=f"facade:{facade.value}",
            message=(
                f"LEGO window anchoring changes the {facade.value} facade rhythm for openings "
                f"[{opening_ids}]: maximum margin/gap distortion is "
                f"{metric.max_segment_distortion * 100:.1f}% of facade width and mean distortion is "
                f"{metric.mean_segment_distortion * 100:.1f}%. Architectural opening geometry remains unchanged."
            ),
        ))
    return issues
