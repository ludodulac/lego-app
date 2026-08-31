"""Assembly analysis using a conservative spatial broad phase."""

from __future__ import annotations

from collections.abc import Sequence

from .core import (
    AssemblyReport,
    CONTACT_EPS,
    PartInstance,
    Relation,
    check_collision,
    find_connections,
)
from .spatial import candidate_pairs


def _validate_instance_ids(parts: Sequence[PartInstance]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for part in parts:
        if part.instance_id in seen:
            duplicates.add(part.instance_id)
        seen.add(part.instance_id)
    if duplicates:
        duplicate_list = ", ".join(repr(value) for value in sorted(duplicates))
        raise ValueError(f"Assembly instance_id values must be unique; duplicates: {duplicate_list}")


def analyze_assembly(parts: Sequence[PartInstance]) -> AssemblyReport:
    """Analyze collisions, contacts, connections, and support topology.

    LDraw meshes include studs and anti-stud cavities. At an exact legal mating
    transform those surfaces can numerically look like a narrow solid
    intersection after a rigid rotation even though the connector model proves
    the parts are on the same nominal mating plane. Connector compatibility is
    therefore evaluated before classifying a mesh intersection as an assembly
    collision. A coincident or genuinely misplaced pair has no exact compatible
    connector match and remains a collision.
    """
    _validate_instance_ids(parts)

    collisions = []
    contacts = []
    connections = []
    graph = {part.instance_id: set() for part in parts}

    for a, b in candidate_pairs(parts):
        pair_connections = find_connections(a, b)
        relation = check_collision(a, b)

        if relation is Relation.COLLISION and not pair_connections:
            collisions.append(
                {
                    "part_a": a.instance_id,
                    "part_b": b.instance_id,
                    "type": "solid_intersection",
                }
            )
        elif relation is Relation.CONTACT or pair_connections:
            # An exact connector mating is a physical contact even when the raw
            # triangulated stud/cavity surfaces produce a rotationally sensitive
            # narrow-phase COLLISION result.
            contacts.append(
                {
                    "part_a": a.instance_id,
                    "part_b": b.instance_id,
                    "type": "connector_contact" if pair_connections else "surface_contact",
                }
            )
            graph[a.instance_id].add(b.instance_id)
            graph[b.instance_id].add(a.instance_id)

        connections.extend(pair_connections)
        if pair_connections:
            graph[a.instance_id].add(b.instance_id)
            graph[b.instance_id].add(a.instance_id)

    if parts:
        base = max(part.bbox.maximum[1] for part in parts)
        roots = {
            part.instance_id
            for part in parts
            if abs(part.bbox.maximum[1] - base) <= CONTACT_EPS
        }
    else:
        roots = set()

    supported = set(roots)
    frontier = list(roots)
    while frontier:
        node = frontier.pop()
        for neighbor in graph[node]:
            if neighbor not in supported:
                supported.add(neighbor)
                frontier.append(neighbor)

    unsupported = [
        part.instance_id for part in parts if part.instance_id not in supported
    ]

    components = []
    unseen = set(graph)
    while unseen:
        start = next(iter(unseen))
        component = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            unseen.discard(node)
            stack.extend(graph[node] - component)
        components.append(sorted(component))

    return AssemblyReport(
        not collisions and not unsupported,
        collisions,
        contacts,
        connections,
        unsupported,
        sorted(components),
    )
