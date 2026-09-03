from types import SimpleNamespace

import pytest

from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.building.models import Facade, OpeningType, OpeningVisualDescription


def _shell(facade: Facade, *, width_studs: int = 2):
    raster = SimpleNamespace(
        id="window-a",
        x_studs=5,
        width_studs=width_studs,
        z_bricks=3,
        height_bricks=2,
    )
    walls = []
    for current in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        wall_width = 20 if current in {Facade.FRONT, Facade.REAR} else 16
        walls.append(
            SimpleNamespace(
                facade=current,
                grid=SimpleNamespace(
                    width_studs=wall_width,
                    height_bricks=12,
                    openings=[raster] if current is facade else [],
                ),
            )
        )
    return SimpleNamespace(walls=walls)


def _building(
    *,
    sill: bool,
    surround: bool = True,
    sill_description: str | None = None,
    sill_color: str | None = None,
):
    opening = SimpleNamespace(
        id="window-a",
        type=OpeningType.WINDOW,
        has_sill=sill,
        has_decorative_surround=surround,
        opening_visual=SimpleNamespace(
            sill=sill_description,
            sill_color=sill_color,
            surround_material="stone",
            surround_color="cream",
        ),
    )
    return SimpleNamespace(openings=[opening])


@pytest.mark.parametrize(
    ("facade", "expected_anchor", "expected_rotation"),
    [
        (Facade.FRONT, (4, 0), 1),
        (Facade.REAR, (12, 15), 1),
        (Facade.RIGHT, (19, 4), 0),
        (Facade.LEFT, (0, 8), 0),
    ],
)
def test_surround_head_includes_both_jamb_corner_cells_on_every_facade(
    facade,
    expected_anchor,
    expected_rotation,
) -> None:
    placements = generate_window_surrounds(_building(sill=False), _shell(facade))

    heads = [part for part in placements if part.trim_role == "head"]
    assert len(heads) == 1
    head = heads[0]
    assert head.part_id == "BRICK_1X4"
    assert (head.x_studs, head.y_studs) == expected_anchor
    assert head.z_plates == 15
    assert head.rotation_quarter_turns == expected_rotation
    assert head.category == "stone"
    assert head.semantic_color == "cream"

    bases = [part for part in placements if part.trim_role == "surround_base"]
    assert len(bases) == 1
    assert bases[0].part_id == "BRICK_1X4"


def test_narrow_surround_keeps_complete_three_cell_head_and_base() -> None:
    placements = generate_window_surrounds(
        _building(sill=False),
        _shell(Facade.FRONT, width_studs=1),
    )

    assert [part.part_id for part in placements if part.trim_role == "head"] == ["BRICK_1X3"]
    assert [part.part_id for part in placements if part.trim_role == "surround_base"] == ["BRICK_1X3"]


def test_sill_replaces_only_surround_base_and_keeps_lower_jamb_corners() -> None:
    placements = generate_window_surrounds(_building(sill=True), _shell(Facade.FRONT))

    assert not [part for part in placements if part.trim_role == "surround_base"]

    sill = [part for part in placements if part.trim_role == "sill"]
    assert len(sill) == 1
    assert sill[0].part_id == "BRICK_1X2"
    assert (sill[0].x_studs, sill[0].y_studs, sill[0].z_plates) == (5, 0, 6)
    assert sill[0].category == "facade_detail"
    assert sill[0].semantic_color is None

    lower_corners = {
        (part.x_studs, part.y_studs, part.z_plates, part.trim_role, part.category, part.semantic_color)
        for part in placements
        if part.z_plates == 6 and part.trim_role in {"left_jamb", "right_jamb"}
    }
    assert lower_corners == {
        (4, 0, 6, "left_jamb", "stone", "cream"),
        (7, 0, 6, "right_jamb", "stone", "cream"),
    }


@pytest.mark.parametrize(
    ("description", "expected_category"),
    [
        ("stone", "stone"),
        ("natural-stone", "stone"),
        ("dressed stone", "stone"),
        ("masonry", "masonry"),
        ("rendered masonry", "masonry"),
    ],
)
def test_sill_preserves_explicit_structured_material_without_changing_geometry(
    description,
    expected_category,
) -> None:
    placements = generate_window_surrounds(
        _building(sill=True, surround=False, sill_description=description),
        _shell(Facade.FRONT),
    )

    sill = [part for part in placements if part.trim_role == "sill"]
    assert len(sill) == 1
    assert sill[0].part_id == "BRICK_1X2"
    assert (sill[0].x_studs, sill[0].y_studs, sill[0].z_plates) == (5, 0, 6)
    assert sill[0].rotation_quarter_turns == 1
    assert sill[0].category == expected_category
    assert sill[0].semantic_color is None


@pytest.mark.parametrize("description", ["stone_like", "cream stone", "painted concrete"])
def test_sill_does_not_promote_ambiguous_or_appearance_only_descriptors(description) -> None:
    placements = generate_window_surrounds(
        _building(sill=True, surround=False, sill_description=description),
        _shell(Facade.FRONT),
    )

    sill = [part for part in placements if part.trim_role == "sill"]
    assert len(sill) == 1
    assert sill[0].category == "facade_detail"


def test_structured_sill_color_round_trips_through_opening_visual_contract() -> None:
    visual = OpeningVisualDescription(sill="stone", sill_color="warm_gray")

    dumped = visual.model_dump()
    assert dumped["sill"] == "stone"
    assert dumped["sill_color"] == "warm_gray"
    assert OpeningVisualDescription.model_validate(dumped).sill_color == "warm_gray"


def test_sill_color_changes_only_semantics_not_geometry_or_part_selection() -> None:
    without_color = generate_window_surrounds(
        _building(sill=True, surround=False, sill_description="stone"),
        _shell(Facade.FRONT),
    )
    with_color = generate_window_surrounds(
        _building(
            sill=True,
            surround=False,
            sill_description="stone",
            sill_color="warm_gray",
        ),
        _shell(Facade.FRONT),
    )

    def geometry(parts):
        return [
            (
                part.part_id,
                part.category,
                part.facade,
                part.x_studs,
                part.y_studs,
                part.z_plates,
                part.rotation_quarter_turns,
                part.opening_id,
                part.trim_role,
            )
            for part in parts
        ]

    assert geometry(with_color) == geometry(without_color)
    assert [part.semantic_color for part in without_color] == [None]
    assert [part.semantic_color for part in with_color] == ["warm_gray"]


def test_sill_color_does_not_bleed_into_surround_color() -> None:
    placements = generate_window_surrounds(
        _building(sill=True, surround=True, sill_color="warm_gray"),
        _shell(Facade.FRONT),
    )

    sill = [part for part in placements if part.trim_role == "sill"]
    surround = [part for part in placements if part.trim_role != "sill"]
    assert sill and surround
    assert {part.semantic_color for part in sill} == {"warm_gray"}
    assert {part.semantic_color for part in surround} == {"cream"}


@pytest.mark.parametrize("sill_color", [None, "", "   "])
def test_missing_or_blank_sill_color_preserves_none_semantics(sill_color) -> None:
    placements = generate_window_surrounds(
        _building(sill=True, surround=False, sill_color=sill_color),
        _shell(Facade.FRONT),
    )

    sill = [part for part in placements if part.trim_role == "sill"]
    assert len(sill) == 1
    assert sill[0].semantic_color is None


def test_existing_surround_stone_like_semantics_are_preserved() -> None:
    building = _building(sill=False)
    building.openings[0].opening_visual.surround_material = "stone_like"

    placements = generate_window_surrounds(building, _shell(Facade.FRONT))

    surround = [part for part in placements if part.trim_role != "sill"]
    assert surround
    assert {part.category for part in surround} == {"masonry"}


def test_surround_never_fills_the_window_void() -> None:
    placements = generate_window_surrounds(_building(sill=True), _shell(Facade.FRONT))

    occupied = set()
    spans = {
        "BRICK_1X1": 1,
        "BRICK_1X2": 2,
        "BRICK_1X3": 3,
        "BRICK_1X4": 4,
        "BRICK_1X6": 6,
        "BRICK_1X8": 8,
    }
    for part in placements:
        span = spans[part.part_id]
        if part.rotation_quarter_turns % 2:
            occupied.update((part.x_studs + offset, part.z_plates // 3) for offset in range(span))
        else:
            occupied.add((part.x_studs, part.z_plates // 3))

    window_void = {(x, course) for x in (5, 6) for course in (3, 4)}
    assert occupied.isdisjoint(window_void)
