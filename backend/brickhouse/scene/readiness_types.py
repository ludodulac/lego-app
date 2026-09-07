"""Compatibility import path for downstream readiness consumers.

This module intentionally contains no ArchitecturalScene schema fields.
"""
from .readiness import ArchitecturalReadinessBlocker, ArchitecturalReadinessReport

__all__ = ["ArchitecturalReadinessBlocker", "ArchitecturalReadinessReport"]
