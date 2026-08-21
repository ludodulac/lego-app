from brickhouse.bricks.windows import _to_global
from brickhouse.building.models import Facade


def test_front_local_offset_is_preserved_in_backend_coordinates() -> None:
    low = _to_global(Facade.FRONT, 2, 2, 1, 20, 18)
    high = _to_global(Facade.FRONT, 12, 2, 1, 20, 18)
    assert low[0] == 2
    assert high[0] == 12
    assert low[0] < high[0]


def test_right_local_offset_increases_from_front_to_rear() -> None:
    near_front = _to_global(Facade.RIGHT, 2, 2, 1, 20, 18)
    near_rear = _to_global(Facade.RIGHT, 12, 2, 1, 20, 18)
    assert near_front[1] == 2
    assert near_rear[1] == 12
    assert near_front[1] < near_rear[1]


def test_left_facade_reverses_local_offset_into_global_y_by_design() -> None:
    near_front = _to_global(Facade.LEFT, 12, 2, 1, 20, 18)
    near_rear = _to_global(Facade.LEFT, 2, 2, 1, 20, 18)
    assert near_front[1] < near_rear[1]
