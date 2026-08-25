"""Generate deterministic architectural surfaces from a BuildingModel."""

from __future__ import annotations

from math import radians, tan

from brickhouse.building.models import BuildingModel, Facade, RidgeDirection, RoofType, Volume

from .models import BuildingGeometry, OpeningGeometry, Point3D, RoofPlaneGeometry, WallGeometry


def _point(x: float, y: float, z: float) -> Point3D:
    return Point3D(x=x, y=y, z=z)


def _wall_corners(volume: Volume, facade: Facade) -> list[Point3D]:
    x0, y0, z0 = volume.position.x, volume.position.y, volume.position.z
    x1, y1, z1 = x0 + volume.width, y0 + volume.depth, z0 + volume.height
    if facade is Facade.FRONT:
        return [_point(x0, y0, z0), _point(x1, y0, z0), _point(x1, y0, z1), _point(x0, y0, z1)]
    if facade is Facade.REAR:
        return [_point(x1, y1, z0), _point(x0, y1, z0), _point(x0, y1, z1), _point(x1, y1, z1)]
    if facade is Facade.LEFT:
        return [_point(x0, y1, z0), _point(x0, y0, z0), _point(x0, y0, z1), _point(x0, y1, z1)]
    return [_point(x1, y0, z0), _point(x1, y1, z0), _point(x1, y1, z1), _point(x1, y0, z1)]


def _opening_corners(volume: Volume, opening) -> list[Point3D]:
    x0, y0, z0 = volume.position.x, volume.position.y, volume.position.z
    h0 = opening.offset_horizontal
    h1 = h0 + opening.width
    z_low = z0 + opening.offset_vertical
    z_high = z_low + opening.height
    if opening.facade is Facade.FRONT:
        return [_point(x0+h0,y0,z_low),_point(x0+h1,y0,z_low),_point(x0+h1,y0,z_high),_point(x0+h0,y0,z_high)]
    if opening.facade is Facade.REAR:
        return [_point(x0+volume.width-h0,y0+volume.depth,z_low),_point(x0+volume.width-h1,y0+volume.depth,z_low),_point(x0+volume.width-h1,y0+volume.depth,z_high),_point(x0+volume.width-h0,y0+volume.depth,z_high)]
    if opening.facade is Facade.LEFT:
        return [_point(x0,y0+volume.depth-h0,z_low),_point(x0,y0+volume.depth-h1,z_low),_point(x0,y0+volume.depth-h1,z_high),_point(x0,y0+volume.depth-h0,z_high)]
    return [_point(x0+volume.width,y0+h0,z_low),_point(x0+volume.width,y0+h1,z_low),_point(x0+volume.width,y0+h1,z_high),_point(x0+volume.width,y0+h0,z_high)]


def _shed_plane(volume: Volume, roof, x0: float, y0: float, x1: float, y1: float, eave_z: float) -> RoofPlaneGeometry:
    assert roof.pitch_degrees is not None
    assert roof.down_slope_direction is not None
    pitch = radians(roof.pitch_degrees)
    direction = roof.down_slope_direction
    run = (volume.depth + 2 * roof.overhang) if direction in {Facade.FRONT, Facade.REAR} else (volume.width + 2 * roof.overhang)
    high_z = eave_z + tan(pitch) * run
    if direction is Facade.REAR:
        corners = [_point(x0,y0,high_z),_point(x1,y0,high_z),_point(x1,y1,eave_z),_point(x0,y1,eave_z)]
    elif direction is Facade.FRONT:
        corners = [_point(x0,y0,eave_z),_point(x1,y0,eave_z),_point(x1,y1,high_z),_point(x0,y1,high_z)]
    elif direction is Facade.RIGHT:
        corners = [_point(x0,y0,high_z),_point(x1,y0,eave_z),_point(x1,y1,eave_z),_point(x0,y1,high_z)]
    else:
        corners = [_point(x0,y0,eave_z),_point(x1,y0,high_z),_point(x1,y1,high_z),_point(x0,y1,eave_z)]
    return RoofPlaneGeometry(id=f"{roof.id}:slope",roof_id=roof.id,volume_id=volume.id,roof_type=roof.type,side="slope",down_slope_direction=direction,corners=corners)


def _roof_planes(volume: Volume, roof) -> list[RoofPlaneGeometry]:
    overhang = roof.overhang
    x0 = volume.position.x - overhang
    y0 = volume.position.y - overhang
    x1 = volume.position.x + volume.width + overhang
    y1 = volume.position.y + volume.depth + overhang
    eave_z = volume.position.z + volume.height
    if roof.type is RoofType.FLAT:
        return [RoofPlaneGeometry(id=f"{roof.id}:flat",roof_id=roof.id,volume_id=volume.id,roof_type=roof.type,side="flat",corners=[_point(x0,y0,eave_z),_point(x1,y0,eave_z),_point(x1,y1,eave_z),_point(x0,y1,eave_z)])]
    if roof.type is RoofType.SHED:
        return [_shed_plane(volume, roof, x0, y0, x1, y1, eave_z)]
    assert roof.pitch_degrees is not None
    assert roof.ridge_direction is not None
    pitch = radians(roof.pitch_degrees)
    if roof.ridge_direction is RidgeDirection.DEPTH:
        ridge_x = volume.position.x + volume.width / 2
        ridge_z = eave_z + tan(pitch) * (volume.width / 2 + overhang)
        return [
            RoofPlaneGeometry(id=f"{roof.id}:negative",roof_id=roof.id,volume_id=volume.id,roof_type=roof.type,side="negative",ridge_direction=roof.ridge_direction,corners=[_point(x0,y0,eave_z),_point(ridge_x,y0,ridge_z),_point(ridge_x,y1,ridge_z),_point(x0,y1,eave_z)]),
            RoofPlaneGeometry(id=f"{roof.id}:positive",roof_id=roof.id,volume_id=volume.id,roof_type=roof.type,side="positive",ridge_direction=roof.ridge_direction,corners=[_point(ridge_x,y0,ridge_z),_point(x1,y0,eave_z),_point(x1,y1,eave_z),_point(ridge_x,y1,ridge_z)]),
        ]
    ridge_y = volume.position.y + volume.depth / 2
    ridge_z = eave_z + tan(pitch) * (volume.depth / 2 + overhang)
    return [
        RoofPlaneGeometry(id=f"{roof.id}:negative",roof_id=roof.id,volume_id=volume.id,roof_type=roof.type,side="negative",ridge_direction=roof.ridge_direction,corners=[_point(x0,y0,eave_z),_point(x1,y0,eave_z),_point(x1,ridge_y,ridge_z),_point(x0,ridge_y,ridge_z)]),
        RoofPlaneGeometry(id=f"{roof.id}:positive",roof_id=roof.id,volume_id=volume.id,roof_type=roof.type,side="positive",ridge_direction=roof.ridge_direction,corners=[_point(x0,ridge_y,ridge_z),_point(x1,ridge_y,ridge_z),_point(x1,y1,eave_z),_point(x0,y1,eave_z)]),
    ]


def generate_building_geometry(model: BuildingModel) -> BuildingGeometry:
    """Convert a validated BuildingModel into deterministic architectural surfaces."""
    openings_by_wall: dict[tuple[str, Facade], list] = {}
    for opening in model.openings:
        openings_by_wall.setdefault((opening.volume_id, opening.facade), []).append(opening)
    walls: list[WallGeometry] = []
    for volume in model.volumes:
        for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
            opening_geometries = [OpeningGeometry(id=opening.id,opening_type=opening.type,volume_id=volume.id,facade=facade,corners=_opening_corners(volume, opening)) for opening in openings_by_wall.get((volume.id, facade), [])]
            walls.append(WallGeometry(id=f"{volume.id}:{facade.value}",volume_id=volume.id,facade=facade,corners=_wall_corners(volume, facade),openings=opening_geometries))
    volume_by_id = {volume.id: volume for volume in model.volumes}
    roof_planes: list[RoofPlaneGeometry] = []
    for roof in model.roofs:
        roof_planes.extend(_roof_planes(volume_by_id[roof.volume_id], roof))
    return BuildingGeometry(building_id=model.id, walls=walls, roof_planes=roof_planes)
