import pytest
from pydantic import ValidationError

from brickhouse.building.models import BuildingModel
from brickhouse.geometry import (
    ArchitecturalSurface,
    ArchitecturalSurfaceKind,
    ArchitecturalSurfaceRole,
    Point3D,
    SurfaceTriangle,
    generate_building_geometry,
    surface_model_from_building_geometry,
)


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _building() -> BuildingModel:
    return BuildingModel.model_validate({
        "schema_version": "0.1",
        "id": "generic-building",
        "name": "Generic building",
        "building_type": "building",
        "units": "m",
        "volumes": [{
            "id": "main",
            "shape": "rectangular_prism",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": 10,
            "depth": 8,
            "height": 6,
            "floors": 2,
            "source": SOURCE,
        }],
        "openings": [{
            "id": "w1",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2,
            "offset_vertical": 2,
            "width": 1.5,
            "height": 1.5,
            "source": SOURCE,
        }],
        "roofs": [{
            "id": "r1",
            "volume_id": "main",
            "type": "gable",
            "overhang": 0.2,
            "ridge_direction": "depth",
            "pitch_degrees": 35,
            "source": SOURCE,
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
        "metadata": {"created_from": "photo_analysis"},
    })


def test_rectilinear_geometry_lifts_losslessly_to_generic_surfaces():
    geometry = generate_building_geometry(_building())
    model = surface_model_from_building_geometry(geometry)
    assert model.building_id == "generic-building"
    assert len([s for s in model.surfaces if s.role is ArchitecturalSurfaceRole.WALL]) == 4
    assert len([s for s in model.surfaces if s.role is ArchitecturalSurfaceRole.ROOF]) == 2
    glazing = [s for s in model.surfaces if s.role is ArchitecturalSurfaceRole.GLAZING]
    assert len(glazing) == 1
    assert glazing[0].facade_hint.value == "front"
    assert all(s.kind is ArchitecturalSurfaceKind.PLANAR_POLYGON for s in model.surfaces)


def test_generic_surface_can_represent_non_rectangular_polygon():
    surface = ArchitecturalSurface(
        id="inclined-facade",
        role="wall",
        kind="planar_polygon",
        vertices=[
            Point3D(x=0, y=0, z=0),
            Point3D(x=5, y=0, z=0),
            Point3D(x=7, y=1, z=6),
            Point3D(x=2, y=1, z=8),
            Point3D(x=-1, y=0.5, z=4),
        ],
    )
    assert len(surface.vertices) == 5
    assert surface.facade_hint is None


def test_generic_surface_can_preserve_triangulated_free_geometry():
    surface = ArchitecturalSurface(
        id="free-envelope",
        role="envelope",
        kind="triangulated_mesh",
        vertices=[
            Point3D(x=0, y=0, z=0),
            Point3D(x=2, y=0, z=0),
            Point3D(x=1, y=1, z=2),
            Point3D(x=1, y=-1, z=2),
        ],
        triangles=[SurfaceTriangle(a=0, b=1, c=2), SurfaceTriangle(a=0, b=3, c=1)],
    )
    assert len(surface.triangles) == 2


def test_mesh_rejects_invalid_triangle_index_instead_of_silently_repairing_geometry():
    with pytest.raises(ValidationError, match="outside the vertex list"):
        ArchitecturalSurface(
            id="bad-mesh",
            role="envelope",
            kind="triangulated_mesh",
            vertices=[
                Point3D(x=0, y=0, z=0),
                Point3D(x=1, y=0, z=0),
                Point3D(x=0, y=1, z=0),
            ],
            triangles=[SurfaceTriangle(a=0, b=1, c=3)],
        )
