import pytest

from brickhouse.bricks.brick_model import (
    _validate_final_gable_roof_host_contact,
    generate_brick_model,
)
from brickhouse.bricks.roof import GlobalRoofPlacement, SpatialRoof
from brickhouse.bricks.spatial import GlobalBrickPlacement, SpatialBrickShell
from brickhouse.building.models import Facade, RidgeDirection


def _shell() -> SpatialBrickShell:
    return SpatialBrickShell(
        building_id="generic-roof-host",
        volume_id="main",
        width_studs=12,
        depth_studs=8,
        height_bricks=4,
        placements=[
            GlobalBrickPlacement(
                brick_id="BRICK_1X4",
                facade=Facade.FRONT,
                x_studs=0,
                y_studs=0,
                z_plates=9,
                rotation_quarter_turns=1,
            ),
            GlobalBrickPlacement(
                brick_id="BRICK_1X4",
                facade=Facade.REAR,
                x_studs=0,
                y_studs=7,
                z_plates=9,
                rotation_quarter_turns=1,
            ),
        ],
    )


def _roof() -> SpatialRoof:
    return SpatialRoof(
        building_id="generic-roof-host",
        roof_id="roof",
        ridge_direction=RidgeDirection.DEPTH,
        placements=[
            GlobalRoofPlacement(
                part_id="BRICK_SLOPED_45_2X4",
                side="negative",
                x_studs=-1,
                y_studs=0,
                z_plates=12,
                rotation_quarter_turns=0,
            ),
            GlobalRoofPlacement(
                part_id="BRICK_SLOPED_45_2X4",
                side="positive",
                x_studs=11,
                y_studs=0,
                z_plates=12,
                rotation_quarter_turns=0,
            ),
            GlobalRoofPlacement(
                part_id="TILE_2X4",
                side="ridge",
                x_studs=5,
                y_studs=0,
                z_plates=15,
                rotation_quarter_turns=0,
            ),
        ],
    )


def test_final_roof_contact_survives_canvas_translation_and_declared_overhang():
    shell = _shell()
    roof = _roof()
    model = generate_brick_model(shell, roof)

    assert model.origin_x_studs == 1
    _validate_final_gable_roof_host_contact(model, shell, roof)


def test_final_roof_contact_rejects_horizontal_detachment_after_translation():
    shell = _shell()
    roof = _roof()
    model = generate_brick_model(shell, roof)
    shifted_parts = [
        part.model_copy(update={"x_studs": part.x_studs + 3})
        if part.component == "roof" and part.roof_side == "negative"
        else part
        for part in model.parts
    ]
    shifted = model.model_copy(update={"parts": shifted_parts})

    with pytest.raises(ValueError, match="lost contact with host boundary"):
        _validate_final_gable_roof_host_contact(shifted, shell, roof)


def test_final_roof_contact_rejects_vertical_floating_eave():
    shell = _shell()
    roof = _roof()
    model = generate_brick_model(shell, roof)
    raised_parts = [
        part.model_copy(update={"z_plates": part.z_plates + 3})
        if part.component == "roof" and part.roof_side == "positive"
        else part
        for part in model.parts
    ]
    raised = model.model_copy(update={"parts": raised_parts})

    with pytest.raises(ValueError, match="expected host wall top"):
        _validate_final_gable_roof_host_contact(raised, shell, roof)
