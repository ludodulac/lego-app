from lego_geometry_engine import AABB, LDrawLibrary


def test_rectangular_brick_connectors_follow_ldraw_length_x_width_z(tmp_path):
    library = LDrawLibrary(tmp_path)
    connectors = tuple(
        library._infer_basic_connectors(
            "Brick 1 x 2",
            AABB((-20.0, -4.0, -10.0), (20.0, 24.0, 10.0)),
        )
    )
    studs = [connector for connector in connectors if connector.type == "stud"]
    anti_studs = [connector for connector in connectors if connector.type == "anti_stud"]

    assert {connector.position for connector in studs} == {
        (-10.0, 0.0, 0.0),
        (10.0, 0.0, 0.0),
    }
    assert {connector.position for connector in anti_studs} == {
        (-10.0, 24.0, 0.0),
        (10.0, 24.0, 0.0),
    }
