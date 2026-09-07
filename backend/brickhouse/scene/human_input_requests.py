"""Derive the smallest explicit human-input list from strict readiness facts.

This layer is intentionally descriptive. It never chooses a missing measurement,
roof direction, pitch, support location, or scale. It only turns already-existing
required-input diagnostics into a deterministic request list for a human.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .readiness import ArchitecturalReadinessReport


HumanInputKind = Literal["exact_metric", "categorical_geometry", "scale_anchor"]


class HumanInputRequest(BaseModel):
    object_id: str
    field: str
    kind: HumanInputKind
    reason: str = Field(min_length=1)
    known_range_degrees: dict[str, float] | None = None
    value: None = None


def _normalized_kind(item: dict[str, Any]) -> HumanInputKind | None:
    kind = item.get("kind")
    if kind in {"exact_metric", "categorical_geometry", "scale_anchor"}:
        return kind
    return None


def derive_minimal_human_input_requests(
    readiness: ArchitecturalReadinessReport,
    required_inputs: list[dict[str, Any]],
) -> list[HumanInputRequest]:
    """Return de-duplicated human requests without synthesizing any answer.

    ``required_inputs`` is the metric/categorical authority because it retains the
    field and input kind produced by the projection boundary. Readiness is used to
    keep requests aligned with the current strict-build decision. Physical-support
    uncertainty that is merely diagnostic is deliberately not converted into a
    measurement request.

    A future caller may pass an explicit ``scale_anchor`` required input when an
    architecture contract proves that one anchor resolves proportional geometry.
    This function never upgrades several exact metrics into a guessed scale anchor.
    """
    required_blockers = {
        (item.object_id, item.field, item.code.removeprefix("required_input:"))
        for item in readiness.blockers
        if item.source == "required_input"
    }

    requests: dict[tuple[str, str, HumanInputKind, str], HumanInputRequest] = {}
    for item in required_inputs:
        object_id = item.get("object_id")
        field = item.get("field")
        reason = item.get("reason")
        kind = _normalized_kind(item)
        if not isinstance(object_id, str) or not object_id:
            continue
        if not isinstance(field, str) or not field:
            continue
        if not isinstance(reason, str) or not reason or kind is None:
            continue

        # When readiness contains required-input blockers, only request items that
        # are part of that current strict decision. This prevents stale diagnostics
        # from leaking into the human checklist.
        if required_blockers and (object_id, field, reason) not in required_blockers:
            continue

        known_range = item.get("known_range_degrees")
        normalized_range = None
        if isinstance(known_range, dict):
            low = known_range.get("min")
            high = known_range.get("max")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                normalized_range = {"min": float(low), "max": float(high)}

        request = HumanInputRequest(
            object_id=object_id,
            field=field,
            kind=kind,
            reason=reason,
            known_range_degrees=normalized_range,
        )
        requests[(object_id, field, kind, reason)] = request

    return sorted(
        requests.values(),
        key=lambda item: (item.object_id, item.field, item.kind, item.reason),
    )
