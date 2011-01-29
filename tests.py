from nose.tools import assert_equals, assert_true

from critters import Dodo


class FakeMap(object):

    def __init__(self, ground_level=-1000):
        self._ground_level = ground_level

    def ground_level(self, x):
        return self._ground_level


class FakeGame(object):

    def __init__(self, game_map):
        self.game_map = game_map


def test_collision_detection_1():
    # air
    #   *
    #    \
    # ----------
    #      \
    #       *
    #     ground
    dodo = Dodo(FakeGame(FakeMap(ground_level=100)))
    dodo.x = 20.0
    dodo.y = 120.0
    dodo.dx = 10.0
    dodo.dy = -50.0
    dodo.update(1.0)
    assert_equals(dodo.x, 24.0)
    assert_equals(dodo.y, 100.0)
    assert_true(dodo.is_alive)
    assert_equals(dodo.dx, 0)
    assert_equals(dodo.dy, 0)


