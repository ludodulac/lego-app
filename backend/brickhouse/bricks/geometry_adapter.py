"""Opt-in bridge from BrickHouse canonical placements to the LDraw geometry engine.

Only canonical parts with a verified LDraw identity and placement rule are mapped.
Unknown architectural/detail parts are never guessed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from lego_geometry_engine import (
    LDrawLibrary,
    PartDefinition,
    PartInstance,
    Transform,
    analyze_assembly,
    instantiate,
)

from .brick_model import BrickModel, BrickModelPart

LDU_PER_STUD = 20.0
LDU_PER_PLATE = 8.0
GEOMETRY_FOOTPRINT_EPS = 1e-4


@dataclass(frozen=True)
class LDrawPartMapping:
    ldraw_id: str
    width_studs: int
    length_studs: int
    height_plates: int = 3
    placement_kind: str = "standard"


CANONICAL_LDRAW_PARTS: Mapping[str, LDrawPartMapping] = {
    "BRICK_1X1": LDrawPartMapping("3005", 1, 1),
    "BRICK_1X2": LDrawPartMapping("3004", 1, 2),
    "BRICK_1X3": LDrawPartMapping("3622", 1, 3),
    "BRICK_1X4": LDrawPartMapping("3010", 1, 4),
    "BRICK_1X6": LDrawPartMapping("3009", 1, 6),
    "BRICK_1X8": LDrawPartMapping("3008", 1, 8),
    "BRICK_2X2": LDrawPartMapping("3003", 2, 2),
    "BRICK_2X3": LDrawPartMapping("3002", 2, 3),
    "BRICK_2X4": LDrawPartMapping("3001", 2, 4),
    "BRICK_2X6": LDrawPartMapping("2456", 2, 6),
    "BRICK_2X8": LDrawPartMapping("3007", 2, 8),
    "BRICK_2X10": LDrawPartMapping("3006", 2, 10),
    # Verified LDraw 45-degree slope family. These need a different placement
    # rule because their LDraw origins are not centered on the footprint.
    "BRICK_SLOPED_45_2X4": LDrawPartMapping("3037", 2, 4, placement_kind="slope_45"),
    "BRICK_SLOPED_45_2X3": LDrawPartMapping("3038", 2, 3, placement_kind="slope_45"),
    "BRICK_SLOPED_45_2X2": LDrawPartMapping("3039", 2, 2, placement_kind="slope_45"),
    "BRICK_SLOPED_45_2X1": LDrawPartMapping("3040b", 2, 1, placement_kind="slope_45"),
}


class UnmappedCanonicalPartError(ValueError):
    pass


@dataclass(frozen=True)
class BrickModelGeometryResult:
    report: object
    mapped_placements: tuple[str, ...]
    unmapped_placements: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.unmapped_placements

    @property
    def valid(self) -> bool:
        return self.complete and bool(getattr(self.report, "valid", False))


def _rotation_matrix(turns: int) -> tuple[tuple[float, float, float], ...]:
    # BrickModel quarter turns rotate in the horizontal grid. LDraw uses X/Z as
    # horizontal axes and -Y as up, so this is a rotation about the LDraw Y axis.
    return (
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)),
        ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)),
        ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    )[turns % 4]


def _transform_from_rotation(rotation, tx: float, ty: float, tz: float) -> Transform:
    return Transform(
        (
            (rotation[0][0], rotation[0][1], rotation[0][2], tx),
            (rotation[1][0], rotation[1][1], rotation[1][2], ty),
            (rotation[2][0], rotation[2][1], rotation[2][2], tz),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def brick_model_part_transform(part: BrickModelPart, mapping: LDrawPartMapping) -> Transform:
    turns = part.rotation_quarter_turns % 4
    footprint_x = mapping.length_studs if turns % 2 else mapping.width_studs
    footprint_z = mapping.width_studs if turns % 2 else mapping.length_studs

    center_x = (part.x_studs + footprint_x / 2.0) * LDU_PER_STUD
    center_z = (part.y_studs + footprint_z / 2.0) * LDU_PER_STUD

    # Canonical BrickModel z_plates is the part's bottom elevation. Standard
    # LDraw bricks have their stud-side top at local Y=0 and extend downward.
    top_y = -(part.z_plates + mapping.height_plates) * LDU_PER_PLATE
    return _transform_from_rotation(_rotation_matrix(turns), center_x, top_y, center_z)


def _rotated_bbox(definition: PartDefinition, turns: int) -> tuple[float, float, float, float]:
    rotation = _rotation_matrix(turns)
    transform = _transform_from_rotation(rotation, 0.0, 0.0, 0.0)
    minimum, maximum = definition.bbox.minimum, definition.bbox.maximum
    corners = [
        transform.point((x, y, z))
        for x in (minimum[0], maximum[0])
        for y in (minimum[1], maximum[1])
        for z in (minimum[2], maximum[2])
    ]
    return (
        min(point[0] for point in corners),
        max(point[0] for point in corners),
        min(point[2] for point in corners),
        max(point[2] for point in corners),
    )


def _slope_45_transform(
    part: BrickModelPart,
    mapping: LDrawPartMapping,
    definition: PartDefinition,
) -> Transform:
    if part.roof_side not in {"negative", "positive"}:
        raise UnmappedCanonicalPartError(
            f"45-degree slope {part.part_id!r} requires roof_side negative/positive "
            f"at placement {part.placement_id!r}"
        )

    # BrickHouse rotation=0 means the roof run is along grid X; rotation=1
    # means the run is along grid Y. LDraw 3037/3038/3039/3040b rise along
    # their local +Z axis. Positive roof sides reverse that rise direction.
    if part.roof_side == "negative":
        physical_turns = (1 - part.rotation_quarter_turns) % 4
    else:
        physical_turns = (3 - part.rotation_quarter_turns) % 4

    rotated_min_x, rotated_max_x, rotated_min_z, rotated_max_z = _rotated_bbox(
        definition, physical_turns
    )
    footprint_x = mapping.length_studs if part.rotation_quarter_turns % 2 else mapping.width_studs
    footprint_z = mapping.width_studs if part.rotation_quarter_turns % 2 else mapping.length_studs
    expected_x = footprint_x * LDU_PER_STUD
    expected_z = footprint_z * LDU_PER_STUD
    actual_x = rotated_max_x - rotated_min_x
    actual_z = rotated_max_z - rotated_min_z
    if abs(actual_x - expected_x) > GEOMETRY_FOOTPRINT_EPS or abs(actual_z - expected_z) > GEOMETRY_FOOTPRINT_EPS:
        raise ValueError(
            f"LDraw footprint mismatch for {part.part_id}: expected "
            f"{expected_x}x{expected_z} LDU, got {actual_x}x{actual_z} LDU"
        )

    target_min_x = part.x_studs * LDU_PER_STUD
    target_min_z = part.y_studs * LDU_PER_STUD
    tx = target_min_x - rotated_min_x
    tz = target_min_z - rotated_min_z
    # Anchor the physical underside/bottom-most mating plane at BrickModel's
    # bottom elevation. Stud protrusions extend toward negative Y and therefore
    # do not disturb this anchor.
    target_bottom_y = -part.z_plates * LDU_PER_PLATE
    ty = target_bottom_y - definition.bbox.maximum[1]
    return _transform_from_rotation(_rotation_matrix(physical_turns), tx, ty, tz)


def brick_model_part_to_instance(part: BrickModelPart, library: LDrawLibrary) -> PartInstance:
    mapping = CANONICAL_LDRAW_PARTS.get(part.part_id)
    if mapping is None:
        raise UnmappedCanonicalPartError(
            f"No verified LDraw mapping for canonical part {part.part_id!r} "
            f"at placement {part.placement_id!r}"
        )
    definition = library.load_part(mapping.ldraw_id)
    if mapping.placement_kind == "slope_45":
        transform = _slope_45_transform(part, mapping, definition)
    else:
        transform = brick_model_part_transform(part, mapping)
    return instantiate(
        definition,
        part.placement_id,
        transform,
        color=part.semantic_color,
    )


def brick_model_to_instances(
    model: BrickModel,
    library: LDrawLibrary,
    *,
    strict: bool = True,
) -> tuple[list[PartInstance], tuple[str, ...]]:
    instances: list[PartInstance] = []
    unmapped: list[str] = []
    for part in model.parts:
        try:
            instances.append(brick_model_part_to_instance(part, library))
        except UnmappedCanonicalPartError:
            if strict:
                raise
            unmapped.append(part.placement_id)
    return instances, tuple(unmapped)


def analyze_brick_model_geometry(
    model: BrickModel,
    library: LDrawLibrary,
    *,
    strict: bool = True,
) -> BrickModelGeometryResult:
    instances, unmapped = brick_model_to_instances(model, library, strict=strict)
    report = analyze_assembly(instances)
    return BrickModelGeometryResult(
        report=report,
        mapped_placements=tuple(instance.instance_id for instance in instances),
        unmapped_placements=unmapped,
    )
