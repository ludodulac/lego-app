"""Backend architectural readiness for strict Scene -> LEGO generation.

Readiness is a behavioral decision derived from existing backend diagnostics.  It
never mutates Survey/ArchitecturalScene and does not promote derived spatial facts
to architectural claims.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from brickhouse.vision.compatibility import M0Compatibility

from .models import ArchitecturalScene, ProjectionResult, ProjectionSeverity
from .spatial_analysis import SpatialRelationReport, analyze_scene_spatial_relations


ReadinessSource = Literal["survey", "projection", "required_input", "m0"]


class ArchitecturalReadinessBlocker(BaseModel):
    code: str
    source: ReadinessSource
    reason: str
    object_id: str | None = None
    field: str | None = None


class ArchitecturalReadinessReport(BaseModel):
    ready_for_lego: bool
    blockers: list[ArchitecturalReadinessBlocker] = Field(default_factory=list)
    spatial: SpatialRelationReport


def _issue_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def assess_architectural_readiness(
    scene: ArchitecturalScene,
    projection: ProjectionResult,
    required_inputs: list[dict[str, Any]],
    compatibility: M0Compatibility | None,
    *,
    survey_issues: list[Any] | None = None,
) -> ArchitecturalReadinessReport:
    """Return one deterministic strict-build decision for every backend caller.

    BH-164 spatial facts are included as diagnostic evidence.  Unknown envelopes
    are intentionally *not* blockers by themselves: a missing metric blocks only
    when projection/required-input diagnostics say a downstream operation needs it.
    """
    blockers: list[ArchitecturalReadinessBlocker] = []

    for issue in survey_issues or []:
        if _issue_value(issue.severity) != "error":
            continue
        blockers.append(
            ArchitecturalReadinessBlocker(
                code=f"survey:{issue.code}",
                source="survey",
                reason=issue.message,
                object_id=getattr(issue, "object_id", None),
            )
        )

    for issue in projection.issues:
        if issue.severity is not ProjectionSeverity.BLOCKER:
            continue
        blockers.append(
            ArchitecturalReadinessBlocker(
                code=f"projection:{issue.code}",
                source="projection",
                reason=issue.message,
                object_id=issue.object_id,
            )
        )

    for item in required_inputs:
        blockers.append(
            ArchitecturalReadinessBlocker(
                code=f"required_input:{item.get('reason', 'missing_input')}",
                source="required_input",
                reason=str(item.get("reason", "required architectural input is missing")),
                object_id=item.get("object_id"),
                field=item.get("field"),
            )
        )

    if compatibility is not None:
        for index, reason in enumerate(compatibility.blockers):
            blockers.append(
                ArchitecturalReadinessBlocker(
                    code=f"m0:compatibility:{index}",
                    source="m0",
                    reason=reason,
                )
            )

    # De-duplicate diagnostics that describe the same blocking fact, then sort so
    # API decisions are stable regardless of incidental producer ordering.
    unique = {
        (item.code, item.source, item.object_id, item.field, item.reason): item
        for item in blockers
    }
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item.source,
            item.code,
            item.object_id or "",
            item.field or "",
            item.reason,
        ),
    )
    return ArchitecturalReadinessReport(
        ready_for_lego=not ordered,
        blockers=ordered,
        spatial=analyze_scene_spatial_relations(scene),
    )
