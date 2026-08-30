"""Conservative sweep-and-prune broad phase for assembly pair discovery."""
from __future__ import annotations

from collections.abc import Iterator, Sequence

from .core import CONTACT_EPS, PartInstance


def candidate_pairs(parts: Sequence[PartInstance]) -> Iterator[tuple[PartInstance, PartInstance]]:
    """Yield every pair whose AABBs can overlap/contact, without false negatives.

    Sorting on X minimum avoids exact mesh work for distant parts. Y/Z checks
    reject remaining separated pairs. check_collision remains the narrow phase.
    """
    ordered = sorted(parts, key=lambda part: part.bbox.minimum[0])
    active: list[PartInstance] = []
    for part in ordered:
        minimum_x = part.bbox.minimum[0]
        active = [other for other in active if other.bbox.maximum[0] >= minimum_x - CONTACT_EPS]
        for other in active:
            if (
                other.bbox.maximum[1] < part.bbox.minimum[1] - CONTACT_EPS
                or part.bbox.maximum[1] < other.bbox.minimum[1] - CONTACT_EPS
                or other.bbox.maximum[2] < part.bbox.minimum[2] - CONTACT_EPS
                or part.bbox.maximum[2] < other.bbox.minimum[2] - CONTACT_EPS
            ):
                continue
            yield other, part
        active.append(part)
