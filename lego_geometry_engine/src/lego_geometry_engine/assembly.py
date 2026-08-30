"""Assembly analysis using a conservative spatial broad phase."""
from __future__ import annotations

from collections.abc import Sequence

from .core import AssemblyReport, CONTACT_EPS, PartInstance, Relation, check_collision, find_connections
from .spatial import candidate_pairs


def analyze_assembly(parts: Sequence[PartInstance]) -> AssemblyReport:
    """Analyze exact relations only for AABB candidates, then build support topology."""
    collisions: list[dict] = []
    contacts: list[dict] = []
    connections: list[dict] = []
    graph = {part.instance_id: set() for part in parts}

    for a, b in candidate_pairs(parts):
        relation = check_collision(a, b)
        if relation is Relation.COLLISION:
            collisions.append({"part_a": a.instance_id, "part_b": b.instance_id, "type": "solid_intersection"})
        elif relation is Relation.CONTACT:
            contacts.append({"part_a": a.instance_id, "part_b": b.instance_id, "type": "surface_contact"})
            graph[a.instance_id].add(b.instance_id)
            graph[b.instance_id].add(a.instance_id)
        pair_connections = find_connections(a, b)
        connections.extend(pair_connections)
        if pair_connections:
            graph[a.instance_id].add(b.instance_id)
            graph[b.instance_id].add(a.instance_id)

    if parts:
        base = max(part.bbox.maximum[1] for part in parts)
        roots = {part.instance_id for part in parts if abs(part.bbox.maximum[1] - base) <= CONTACT_EPS}
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
    unsupported = [part.instance_id for part in parts if part.instance_id not in supported]

    components: list[list[str]] = []
    unseen = set(graph)
    while unseen:
        start = next(iter(unseen))
        component: set[str] = set()
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
