import pytest
from pydantic import ValidationError

from brickhouse.building import Appearance, AppearanceSection, Facade, OpeningType, Position3D, RidgeDirection, RoofType, SourceInfo, SourceKind
from brickhouse.scene import (
    ArchitecturalScene,
    Chimney,
    Evidence,
    FacadeVisibility,
    GradeProfile,
    Platform,
    PropertyValue,
    SceneOpening,
    SceneRoof,
    SceneVolume,
    SupportPost,
    Terrain,
    VisibilitySpan,
    VisibilityState,
    project_scene_to_building,
)


def source(kind=SourceKind.INFERRED, confidence=0.7):
    return SourceInfo(kind=kind, confidence=confidence)


def base_scene(**overrides):
    volume = SceneVolume(
        id="volume_main",
        position=Position3D(x=0, y=0, z=0),
        width=PropertyValue(value=10.0, source=source(SourceKind.USER_PROVIDED, 0.99)),
        depth=PropertyValue(value=10.5, source=source()),
        height=PropertyValue(value=7.8, source=source()),
        floors=3,
        source=source(),
    )
    roof = SceneRoof(
        id="roof_main",
        volume_id="volume_main",
        type=RoofType.GABLE,
        overhang=0.25,
        ridge_direction=RidgeDirection.DEPTH,
        pitch_degrees=10,
        source=source(),
    )
    values = dict(
        schema_version="0.2",
        id="building_photo_001",
        name="Regression building",
        volumes=[volume],
        roofs=[roof],
        appearance=Appearance(
            walls=AppearanceSection(color="light_gray"),
            roof=AppearanceSection(color="dark_gray"),
            frames=AppearanceSection(color="white"),
        ),
    )
    values.update(overrides)
    return ArchitecturalScene(**values)


def test_scene_rejects_opening_in_occluded_span():
    with pytest.raises(ValidationError, match="intersects non-visible facade span"):
        base_scene(
            openings=[SceneOpening(id="rear_hidden", type=OpeningType.WINDOW, volume_id="volume_main", facade=Facade.REAR, offset_horizontal=1.0, offset_vertical=2.0, width=1.0, height=1.2, source=source())],
            visibility=[FacadeVisibility(facade=Facade.REAR, spans=[VisibilitySpan(**{"from": 0.0, "to": 5.0, "state": VisibilityState.OCCLUDED, "by": "neighbor"})])],
        )


def test_scene_rejects_opening_extending_past_facade():
    with pytest.raises(ValidationError, match="extends past facade horizontally"):
        base_scene(openings=[SceneOpening(id="past_corner", type=OpeningType.WINDOW, volume_id="volume_main", facade=Facade.RIGHT, offset_horizontal=10.0, offset_vertical=2.0, width=1.0, height=1.0, source=source())])


def test_scene_rejects_overlapping_openings():
    with pytest.raises(ValidationError, match="overlap"):
        base_scene(openings=[
            SceneOpening(id="a", type=OpeningType.WINDOW, volume_id="volume_main", facade=Facade.FRONT, offset_horizontal=1.0, offset_vertical=2.0, width=1.5, height=1.5, source=source()),
            SceneOpening(id="b", type=OpeningType.WINDOW, volume_id="volume_main", facade=Facade.FRONT, offset_horizontal=2.0, offset_vertical=2.5, width=1.5, height=1.5, source=source()),
        ])


def test_projection_preserves_supported_geometry_and_reports_losses():
    scene = base_scene(
        openings=[SceneOpening(id="workshop_window", type=OpeningType.WINDOW, volume_id="volume_main", facade=Facade.RIGHT, offset_horizontal=6.8, offset_vertical=0.4, width=1.0, height=0.8, source=source(), local_grade_clearance=0.05)],
        terrain=Terrain(profiles=[GradeProfile(facade=Facade.RIGHT, start_elevation=0.0, end_elevation=1.4, source=source(), evidence=[Evidence(photo_index=2, observation="road rises along the right facade")])]),
        chimneys=[Chimney(id="chimney_01", position=Position3D(x=1, y=2, z=7.8), width=0.7, depth=0.7, height=1.6, source=source())],
        platforms=[Platform(id="terrace_left", position=Position3D(x=-2, y=4, z=2.8), width=2.0, depth=4.0, thickness=0.2, supports=[SupportPost(id="terrace_post_01", position=Position3D(x=-1.8, y=4.2, z=0), width=0.2, depth=0.2, height=2.8, source=source())], source=source())],
    )
    result = project_scene_to_building(scene)
    assert result.building is not None
    assert result.building.volumes[0].width == 10.0
    assert result.building.openings[0].id == "workshop_window"
    assert {issue.code for issue in result.issues} == {"terrain_not_supported", "local_grade_clearance_not_supported", "chimney_not_supported", "platform_not_supported"}
    assert result.blocked is False


def test_projection_uses_neutral_building_type_instead_of_house_fixture_bias():
    result = project_scene_to_building(base_scene())
    assert result.building is not None
    assert result.building.building_type == "building"


def _secondary_volume():
    return SceneVolume(
        id="volume_second",
        position=Position3D(x=10, y=0, z=0),
        width=PropertyValue(value=2, source=source()),
        depth=PropertyValue(value=3, source=source()),
        height=PropertyValue(value=2, source=source()),
        floors=1,
        source=source(),
    )


def test_projection_preserves_multiple_volumes():
    second = _secondary_volume()
    scene = base_scene(volumes=[base_scene().volumes[0], second])
    result = project_scene_to_building(scene)
    assert result.building is not None
    assert result.blocked is False
    assert [volume.id for volume in result.building.volumes] == ["volume_main", "volume_second"]


def test_legacy_visibility_without_volume_id_scopes_to_primary_volume_only():
    main = base_scene().volumes[0]
    second = _secondary_volume()
    scene = base_scene(
        volumes=[main, second],
        openings=[SceneOpening(
            id="secondary_rear_window",
            type=OpeningType.WINDOW,
            volume_id="volume_second",
            facade=Facade.REAR,
            offset_horizontal=0.25,
            offset_vertical=0.5,
            width=0.8,
            height=0.9,
            source=source(),
        )],
        visibility=[FacadeVisibility(
            facade=Facade.REAR,
            spans=[VisibilitySpan(**{"from": 0.0, "to": 5.0, "state": VisibilityState.OCCLUDED, "by": "neighbor"})],
        )],
    )
    assert scene.openings[0].id == "secondary_rear_window"


def test_visibility_can_be_defined_independently_for_same_facade_on_two_volumes():
    main = base_scene().volumes[0]
    second = _secondary_volume()
    scene = base_scene(
        volumes=[main, second],
        visibility=[
            FacadeVisibility(
                volume_id="volume_main",
                facade=Facade.REAR,
                spans=[VisibilitySpan(**{"from": 0.0, "to": 5.0, "state": VisibilityState.OCCLUDED})],
            ),
            FacadeVisibility(
                volume_id="volume_second",
                facade=Facade.REAR,
                spans=[VisibilitySpan(**{"from": 0.0, "to": 2.0, "state": VisibilityState.VISIBLE})],
            ),
        ],
    )
    assert len(scene.visibility) == 2


def test_visibility_rejects_unknown_volume_reference():
    with pytest.raises(ValidationError, match="references unknown volume"):
        base_scene(
            visibility=[FacadeVisibility(
                volume_id="missing",
                facade=Facade.FRONT,
                spans=[VisibilitySpan(**{"from": 0.0, "to": 1.0, "state": VisibilityState.VISIBLE})],
            )]
        )
