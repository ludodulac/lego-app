"""Backend architectural readiness for strict Scene -> LEGO generation.

Readiness is a behavioral decision derived from existing backend diagnostics. It
never mutates Survey/ArchitecturalScene and does not promote derived spatial facts
to architectural claims.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from brickhouse.vision.compatibility import M0Compatibility

from .physical_support import analyze_physical_support
from .projection import ProjectionResult, ProjectionSeverity
from .spatial_analysis import SpatialRelationReport, analyze_scene_spatial_relations
from .wall_profile_scene import ArchitecturalScene


ReadinessSource = Literal["survey", "projection", "required_input", "m0", "physical_support"]


class ArchitecturalReadinessBlocker(BaseModel):
    code: str
    source: ReadinessSource
    reason: str
    object_id: str | None = None
    field: str | None = None


class ArchitecturalReadinessDiagnostic(BaseModel):
    code: str
    source: ReadinessSource
    severity: Literal["warning", "info"]
    reason: str
    object_id: str | None = None
    field: str | None = None


class ArchitecturalReadinessReport(BaseModel):
    ready_for_lego: bool
    blockers: list[ArchitecturalReadinessBlocker] = Field(default_factory=list)
    diagnostics: list[ArchitecturalReadinessDiagnostic] = Field(default_factory=list)
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

    BH-164 spatial facts and canonical physical-support facts are included as
    diagnostic evidence. Unknown envelopes/support junctions are intentionally not
    blockers by themselves: they block only when an existing downstream contract
    requires the missing fact. Contradicted physical support is a blocker because a
    strict LEGO build must not emit a known floating/invalid architectural assembly.
    """
    blockers: list[ArchitecturalReadinessBlocker] = []
    diagnostics: list[ArchitecturalReadinessDiagnostic] = []

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

    support_facts, support_issues = analyze_physical_support(scene)
    for issue in support_issues:
        if issue.severity == "blocker":
            blockers.append(
                ArchitecturalReadinessBlocker(
                    code=f"physical_support:{issue.code}",
                    source="physical_support",
                    reason=issue.message,
                    object_id=issue.object_id,
                )
            )
        else:
            diagnostics.append(
                ArchitecturalReadinessDiagnostic(
                    code=f"physical_support:{issue.code}",
                    source="physical_support",
                    severity="warning",
                    reason=issue.message,
                    object_id=issue.object_id,
                )
            )

    for fact in support_facts:
        if fact.state != "unresolved":
            continue
        endpoint = f" endpoint {fact.endpoint}" if fact.endpoint is not None else ""
        supporter = f" relative to {fact.supporter_id!r}" if fact.supporter_id is not None else ""
        diagnostics.append(
            ArchitecturalReadinessDiagnostic(
                code=f"physical_support:unresolved:{fact.kind}",
                source="physical_support",
                severity="warning",
                object_id=fact.object_id,
                reason=(
                    f"Physical support for {fact.kind} on {fact.object_id!r}{endpoint}{supporter} remains unresolved: "
                    f"{fact.reason}. No hidden support or compensating geometry is invented."
                ),
            )
        )

    unique_blockers = {
        (item.code, item.source, item.object_id, item.field, item.reason): item
        for item in blockers
    }
    ordered_blockers = sorted(
        unique_blockers.values(),
        key=lambda item: (
            item.source,
            item.code,
            item.object_id or "",
            item.field or "",
            item.reason,
        ),
    )
    unique_diagnostics = {
        (item.code, item.source, item.severity, item.object_id, item.field, item.reason): item
        for item in diagnostics
    }
    ordered_diagnostics = sorted(
        unique_diagnostics.values(),
        key=lambda item: (
            item.source,
            item.code,
            item.object_id or "",
            item.field or "",
            item.reason,
        ),
    )
    return ArchitecturalReadinessReport(
        ready_for_lego=not ordered_blockers,
        blockers=ordered_blockers,
        diagnostics=ordered_diagnostics,
        spatial=analyze_scene_spatial_relations(scene),
    )
