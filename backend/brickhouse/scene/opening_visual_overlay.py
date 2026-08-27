"""Apply explicit opening-visual observations to an ArchitecturalScene.

The overlay is intentionally narrow: it may enrich only fields already defined by
``OpeningVisualDescription`` and never changes opening geometry, type or position.
This lets independently reviewed photo evidence remain separately versioned while
still feeding deterministic LEGO construction when explicitly requested.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brickhouse.building.models import OpeningVisualDescription

from .models import ArchitecturalScene

_VISUAL_FIELDS = frozenset(OpeningVisualDescription.model_fields)


def apply_opening_visual_evidence(
    scene: ArchitecturalScene,
    evidence: dict[str, Any],
) -> ArchitecturalScene:
    observations = evidence.get("observations")
    if not isinstance(observations, list):
        raise ValueError("opening visual evidence must contain an observations list")

    openings = {opening.id: opening for opening in scene.openings}
    updates = {}
    seen_targets: set[str] = set()
    for index, record in enumerate(observations, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"opening visual observation {index} must be an object")
        target = record.get("scene_opening_id") or record.get("opening_id")
        if not isinstance(target, str) or not target:
            raise ValueError(f"opening visual observation {index} has no target opening id")
        if target not in openings:
            raise ValueError(f"opening visual evidence targets unknown Scene opening {target!r}")
        if target in seen_targets:
            raise ValueError(f"duplicate opening visual evidence for Scene opening {target!r}")
        seen_targets.add(target)

        explicit = {key: record[key] for key in _VISUAL_FIELDS if key in record}
        if not explicit:
            raise ValueError(f"opening visual evidence for {target!r} contains no supported visual fields")
        existing = openings[target].opening_visual
        merged = existing.model_dump(exclude_none=True) if existing is not None else {}
        merged.update(explicit)
        visual = OpeningVisualDescription.model_validate(merged)
        updates[target] = openings[target].model_copy(update={"opening_visual": visual})

    return scene.model_copy(update={
        "openings": [updates.get(opening.id, opening) for opening in scene.openings]
    })


def load_and_apply_opening_visual_evidence(
    scene: ArchitecturalScene,
    path: str | Path,
) -> ArchitecturalScene:
    source = Path(path)
    try:
        evidence = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid opening visual evidence JSON: {exc}") from exc
    if not isinstance(evidence, dict):
        raise ValueError("opening visual evidence root must be an object")
    return apply_opening_visual_evidence(scene, evidence)
