"""Production gate from metric Scene support facts to LEGO augmentation.

The gate is deliberately selective: contradicted exterior assemblies are withheld
from the corresponding Scene augmentation pass while unrelated supported geometry
remains buildable. Unresolved support is surfaced as fidelity uncertainty and is
never repaired with synthetic geometry.
"""
from __future__ import annotations

from dataclasses import dataclass

from brickhouse.scene.physical_support import analyze_physical_support

from .export import BrickExportFidelityIssue


@dataclass(frozen=True)
class ScenePhysicalSupportGate:
    fidelity_issues: tuple[BrickExportFidelityIssue, ...]
    blocked_platform_ids: frozenset[str]
    blocked_stair_ids: frozenset[str]
    blocked_chimney_ids: frozenset[str]

    def platform_scene(self, scene):
        if not self.blocked_platform_ids and not self.blocked_stair_ids:
            return scene
        return scene.model_copy(update={
            "platforms": [item for item in scene.platforms if item.id not in self.blocked_platform_ids],
            "stairs": [item for item in scene.stairs if item.id not in self.blocked_stair_ids],
        })

    def chimney_scene(self, scene):
        if not self.blocked_chimney_ids:
            return scene
        return scene.model_copy(update={
            "chimneys": [item for item in scene.chimneys if item.id not in self.blocked_chimney_ids],
        })


def evaluate_scene_physical_support_gate(scene) -> ScenePhysicalSupportGate:
    """Translate support truth into deterministic production diagnostics/gating."""
    facts, support_issues = analyze_physical_support(scene)
    platform_ids = {item.id for item in scene.platforms}
    stair_ids = {item.id for item in scene.stairs}
    chimney_ids = {item.id for item in scene.chimneys}

    blocked_platform_ids: set[str] = set()
    blocked_stair_ids: set[str] = set()
    blocked_chimney_ids: set[str] = set()
    issues: list[BrickExportFidelityIssue] = []

    for issue in support_issues:
        issues.append(BrickExportFidelityIssue(
            code=issue.code,
            severity=issue.severity,
            object_id=issue.object_id,
            message=issue.message,
        ))
        if issue.severity != "blocker":
            continue
        if issue.object_id in platform_ids:
            blocked_platform_ids.add(issue.object_id)
        if issue.object_id in stair_ids:
            blocked_stair_ids.add(issue.object_id)
        if issue.object_id in chimney_ids:
            blocked_chimney_ids.add(issue.object_id)

    for fact in facts:
        if fact.state == "unresolved":
            endpoint = f" endpoint {fact.endpoint}" if fact.endpoint is not None else ""
            supporter = f" relative to {fact.supporter_id!r}" if fact.supporter_id is not None else ""
            issues.append(BrickExportFidelityIssue(
                code="physical_support_unresolved",
                severity="warning",
                object_id=fact.object_id,
                message=(
                    f"Physical support for {fact.kind} on {fact.object_id!r}{endpoint}{supporter} remains unresolved: "
                    f"{fact.reason}. No hidden support or compensating geometry is invented."
                ),
            ))
            continue
        if fact.state != "contradicted":
            continue

        # A contradicted direct fact blocks the architectural assembly it describes.
        if fact.object_id in platform_ids:
            blocked_platform_ids.add(fact.object_id)
        if fact.object_id in stair_ids:
            blocked_stair_ids.add(fact.object_id)
        if fact.object_id in chimney_ids:
            blocked_chimney_ids.add(fact.object_id)

        # For an explicit support relation, the supporter can itself be the unsafe
        # generated assembly (for example a platform claimed to support a volume).
        if fact.kind == "explicit_support_relation" and fact.supporter_id in platform_ids:
            blocked_platform_ids.add(fact.supporter_id)
        if fact.kind == "explicit_support_relation" and fact.supporter_id in stair_ids:
            blocked_stair_ids.add(fact.supporter_id)
        if fact.kind == "explicit_support_relation" and fact.supporter_id in chimney_ids:
            blocked_chimney_ids.add(fact.supporter_id)

    # Deterministic de-duplication: analyzer issues and fact-derived uncertainty can
    # converge on the same object without multiplying identical export diagnostics.
    unique: list[BrickExportFidelityIssue] = []
    seen: set[tuple[str, str | None, str]] = set()
    for issue in issues:
        key = (issue.code, issue.object_id, issue.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)

    return ScenePhysicalSupportGate(
        fidelity_issues=tuple(unique),
        blocked_platform_ids=frozenset(blocked_platform_ids),
        blocked_stair_ids=frozenset(blocked_stair_ids),
        blocked_chimney_ids=frozenset(blocked_chimney_ids),
    )
