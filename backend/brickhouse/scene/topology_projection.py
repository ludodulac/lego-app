"""Topology-aware projection entry point.

Topological certainty is enforced in the core projection function so every
caller, including the full viewer pipeline, shares the same blocker semantics.
"""
from __future__ import annotations

from .projection import (
    ProjectionResult,
    project_scene_to_building as _project_scene_to_building,
)
from .topology import ArchitecturalScene


def project_scene_to_building(scene: ArchitecturalScene) -> ProjectionResult:
    return _project_scene_to_building(scene)
