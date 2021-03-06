import sys

from nose.tools import assert_equals, assert_true, assert_false


# --- zomg stubs ---

class FakePygletGl(object):
    GL_ALL_ATTRIB_BITS = None

class FakePygletWindow(object):
    key = None
    class Window(object):
        def __init__(self, *a, **kw):
            pass

class FakePygletImage(object):
    class Image(object):
        pass
    class Animation(object):
        @classmethod
        def from_image_sequence(self, *a, **kw):
            return FakePygletImage.Image()

class FakePygletResource(object):
    path = None

    def image(self, filename):
        return FakePygletImage.Image()
    def media(self, filename, streaming=True):
        return None
    def reindex(self):
        pass

class FakePygletSprite(object):
    class Sprite(object):
        def __init__(self, image, **kw):
            self.image = image

class FakePygletMedia(object):
    class Player(object):
        def queue(self, source):
            pass
        def play(self):
            pass
        def next(self):
            pass
        def seek(self, where):
            pass

class FakePygletClock(object):
    def schedule_once(self, fn, when):
        pass

class FakePyglet(object):
    gl = FakePygletGl()
    window = FakePygletWindow()
    resource = FakePygletResource()
    sprite = FakePygletSprite()
    image = FakePygletImage()
    media = FakePygletMedia()
    clock = FakePygletClock()

sys.modules['pyglet'] = FakePyglet()
sys.modules['pyglet.window'] = FakePyglet.window

# -- end of zomg stubs --

from dodo import Dodo


class FakeMap(object):

    def __init__(self, ground_level=0, wall_x=0):
        self._ground_level = ground_level
        self._wall_x = wall_x

    def ground_level(self, x):
        if x < self._wall_x:
            return 0
        else:
            return self._ground_level

    def vertical_wall_left_of(self, x):
        if x >= self._wall_x:
            return self._wall_x
        else:
            return 0


class FakeCamera(object):
    def remove_focus(self, obj):
        pass


class FakeGame(object):

    dodo_batch = None
    camera = FakeCamera()

    def __init__(self, game_map):
        self.game_map = game_map

    def count_surviving_dodos(self):
        pass


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


def test_collision_detection_2():
    # air
    #   *
    #    \
    #    +------
    #    | \
    #    |  *
    #    |ground
    dodo = Dodo(FakeGame(FakeMap(ground_level=100, wall_x=22)))
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


def test_collision_detection_3():
    # air
    #   *
    #    \+-------
    #     |
    #     |\
    #     | *
    # ----+ ground 
    dodo = Dodo(FakeGame(FakeMap(ground_level=100, wall_x=40)))
    dodo.x = 20.0
    dodo.y = 120.0
    dodo.dx = 40.0
    dodo.dy = -50.0
    dodo.update(1.0)
    assert_equals(dodo.x, 40.0)
    assert_equals(dodo.y, 95.0)
    assert_false(dodo.is_alive)
    assert_equals(dodo.dx, 0)
    assert_equals(dodo.dy, 0)


def test_collision_detection_4():
    #     +-------
    #     | *
    #     |/
    #     |
    #    /|
    #   * |
    # ----+ ground 
    dodo = Dodo(FakeGame(FakeMap(ground_level=200, wall_x=40)))
    dodo.x = 20.0
    dodo.y = 30.0
    dodo.dx = 40.0
    dodo.dy = 50.0
    dodo.update(1.0)
    assert_equals((dodo.x, dodo.y), (40.0, 55))
    assert_false(dodo.is_alive)
    assert_equals(dodo.dx, 0)
    assert_equals(dodo.dy, 0)


def test_collision_detection_5():
    # extracted from a real crash
    dodo = Dodo(FakeGame(FakeMap(ground_level=710, wall_x=720)))
    dodo.x = 720.0
    dodo.y = 495.0
    dodo.dx = 50.0
    dodo.dy = 50.0
    dodo.update(1.0)
    assert_equals(dodo.x, 720.0)
    assert_equals(dodo.y, 495.0)
    assert_false(dodo.is_alive)
    assert_equals(dodo.dx, 0)
    assert_equals(dodo.dy, 0)


def test_collision_detection_launch_inside_wall():
    # extracted from a real crash
    dodo = Dodo(FakeGame(FakeMap(ground_level=710, wall_x=720)))
    dodo.x = 721.0
    dodo.y = 495.0
    dodo.dx = 50.0
    dodo.dy = 50.0
    dodo.update(1.0)
    assert_equals(dodo.x, 721.0)
    assert_equals(dodo.y, 495.0)
    assert_false(dodo.is_alive)
    assert_equals(dodo.dx, 0)
    assert_equals(dodo.dy, 0)

