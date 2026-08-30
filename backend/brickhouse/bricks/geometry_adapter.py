"""Opt-in bridge from BrickHouse canonical placements to the LDraw geometry engine.

This module deliberately maps only canonical parts whose LDraw identity is known.
Unknown architectural/detail/roof parts are never guessed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from lego_geometry_engine import LDrawLibrary, PartInstance, Transform, analyze_assembly, instantiate

from .brick_model import BrickModel, BrickModelPart

LDU_PER_STUD = 20.0
LDU_PER_PLATE = 8.0


@dataclass(frozen=True)
class LDrawPartMapping:
    ldraw_id: str
    width_studs: int
    length_studs: int
    height_plates: int = 3


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


def brick_model_part_transform(part: BrickModelPart, mapping: LDrawPartMapping) -> Transform:
    turns = part.rotation_quarter_turns % 4
    footprint_x = mapping.length_studs if turns % 2 else mapping.width_studs
    footprint_z = mapping.width_studs if turns % 2 else mapping.length_studs

    center_x = (part.x_studs + footprint_x / 2.0) * LDU_PER_STUD
    center_z = (part.y_studs + footprint_z / 2.0) * LDU_PER_STUD

    # Canonical BrickModel z_plates is the part's bottom elevation. Standard
    # LDraw bricks have their stud-side top at local Y=0 and extend downward,
    # hence the translation by the full part height into negative Y.
    top_y = -(part.z_plates + mapping.height_plates) * LDU_PER_PLATE
    rotation = _rotation_matrix(turns)
    return Transform(
        (
            (rotation[0][0], rotation[0][1], rotation[0][2], center_x),
            (rotation[1][0], rotation[1][1], rotation[1][2], top_y),
            (rotation[2][0], rotation[2][1], rotation[2][2], center_z),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def brick_model_part_to_instance(part: BrickModelPart, library: LDrawLibrary) -> PartInstance:
    mapping = CANONICAL_LDRAW_PARTS.get(part.part_id)
    if mapping is None:
        raise UnmappedCanonicalPartError(
            f"No verified LDraw mapping for canonical part {part.part_id!r} "
            f"at placement {part.placement_id!r}"
        )
    definition = library.load_part(mapping.ldraw_id)
    return instantiate(
        definition,
        part.placement_id,
        brick_model_part_transform(part, mapping),
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
