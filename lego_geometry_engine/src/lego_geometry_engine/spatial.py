"""Conservative sweep-and-prune broad phase for assembly pair discovery."""
from __future__ import annotations

from collections.abc import Iterator, Sequence

from .core import AABB, CONTACT_EPS, PartInstance


def _interaction_bounds(part: PartInstance) -> AABB:
    """Union mesh bounds with transformed connector tolerance envelopes."""
    minimum = list(part.bbox.minimum)
    maximum = list(part.bbox.maximum)
    for connector in part.definition.connectors:
        position = part.transform.point(connector.position)
        radius = max(connector.tolerance, CONTACT_EPS)
        for axis in range(3):
            minimum[axis] = min(minimum[axis], position[axis] - radius)
            maximum[axis] = max(maximum[axis], position[axis] + radius)
    return AABB(tuple(minimum), tuple(maximum))


def candidate_pairs(parts: Sequence[PartInstance]) -> Iterator[tuple[PartInstance, PartInstance]]:
    """Yield every pair that can geometrically touch or mate by connector."""
    entries = [(part, _interaction_bounds(part)) for part in parts]
    entries.sort(key=lambda entry: entry[1].minimum[0])
    active: list[tuple[PartInstance, AABB]] = []
    for part, bounds in entries:
        minimum_x = bounds.minimum[0]
        active = [entry for entry in active if entry[1].maximum[0] >= minimum_x - CONTACT_EPS]
        for other, other_bounds in active:
            if (
                other_bounds.maximum[1] < bounds.minimum[1] - CONTACT_EPS
                or bounds.maximum[1] < other_bounds.minimum[1] - CONTACT_EPS
                or other_bounds.maximum[2] < bounds.minimum[2] - CONTACT_EPS
                or bounds.maximum[2] < other_bounds.minimum[2] - CONTACT_EPS
            ):
                continue
            yield other, part
        active.append((part, bounds))
