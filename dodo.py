#!/usr/bin/env python
import os
import math
import random
import logging
import itertools
from contextlib import contextmanager

import pyglet
from pyglet.window import key
from pyglet import gl

from critters import Dodo


log = logging.getLogger('dodo')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


asset_dir = os.path.join(os.path.dirname(__file__), 'assets')


def read_asset(filename):
    with open(os.path.join(asset_dir, filename)) as fp:
        return fp.read()


def load_image(filename):
    return pyglet.image.load(os.path.join(asset_dir, filename))


window = pyglet.window.Window(width=1024, height=600)


@contextmanager
def gl_matrix():
    gl.glPushMatrix()
    try:
        yield
    finally:
        gl.glPopMatrix()


@contextmanager
def gl_state(bits=gl.GL_ALL_ATTRIB_BITS):
    gl.glPushAttrib(bits)
    try:
        yield
    finally:
        gl.glPopAttrib()


class Dodopult(object):

    armed_sprite = loaded_sprite = load_image('Catapult_1.png')

    unarmed_sprite = load_image('Catapult_5.png')

    arming_sprites = [unarmed_sprite,
                      load_image('Catapult_4.png'),
                      load_image('Catapult_3.png'),
                      load_image('Catapult_2.png')]

    reload_delay = 2 # animation duration, seconds

    SPRITE_SCALE = 0.5

    PAYLOAD_POS = (4 * SPRITE_SCALE, 38 * SPRITE_SCALE)
    LAUNCH_POS = (140 * SPRITE_SCALE, 150 * SPRITE_SCALE)

    PICKUP_RANGE = (-15, +15)

    MARGIN_LEFT = -60
    MARGIN_RIGHT = 130

    AIM_R = 50
    AIM_SIZE = 0.15

    INITIAL_X = 500

    min_power = 200.0         # pixels per second
    max_power = 1000.0        # pixels per second
    power_increase = 200.0    # pixels per second per second

    aim_angle = 45
    min_aim_angle = 15
    max_aim_angle = 75

    def __init__(self, game):
        self.game = game
        self.sprite = pyglet.sprite.Sprite(self.armed_sprite)
        self.sprite.scale = self.SPRITE_SCALE
        self.payload = None
        self.armed = True
        self.time_loading = 0
        self.power = self.min_power
        self.powering_up = False

        doc = pyglet.text.document.UnformattedDocument('*\n' * 21)
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 20,
                    'line_spacing': 12,
                    'color': (255, 255, 255, 255)
                })
        self.power_bar = pyglet.text.layout.TextLayout(doc, 100, 800,
                                                       multiline=True)
        self.power_bar.anchor_y = 'top'
        self.power_bar.x = 20
        self.power_bar.y = window.height - 30

    @property
    def x(self):
        return self.sprite.x

    @x.setter
    def x(self, x):
        self.sprite.x = x
        if self.payload:
            self.payload.x = x + self.PAYLOAD_POS[0]

    @property
    def y(self):
        return self.sprite.y

    @y.setter
    def y(self, y):
        self.sprite.y = y
        if self.payload:
            self.payload.y = y + self.PAYLOAD_POS[1]

    def set_sprite(self, sprite):
        self.sprite.image = sprite

    def update(self, dt):
        power = (self.power - self.min_power) / (self.max_power - self.min_power)
        n1 = 1 + int(power * 20)
        n2 = 21 - n1
        self.power_bar.document.text = ' \n' * n2 +  '*\n' * n1
        if self.powering_up:
            self.power = min(self.power + dt * self.power_increase, self.max_power)
        if not self.armed:
            self.time_loading += dt
            if self.time_loading < self.reload_delay:
                n = int(self.time_loading * len(self.arming_sprites) / self.reload_delay)
                self.set_sprite(self.arming_sprites[n])
            else:
                self.time_loading = 0
                self.armed = True
                self.set_sprite(self.armed_sprite)

    def fire(self):
        if self.armed:
            if self.payload:
                self.payload.x = self.x + self.LAUNCH_POS[0]
                self.payload.y = self.y + self.LAUNCH_POS[1]
                self.payload.launch(*self.aim_vector(self.power))
            self.power = self.min_power
            self.powering_up = False
            self.armed = False
            self.payload = None
            self.set_sprite(self.unarmed_sprite)

    def start_powering_up(self):
        if self.armed:
            self.powering_up = True

    def draw(self):
        with gl_matrix():
            gl.glLoadIdentity()
            self.power_bar.draw()
        self.sprite.draw()
        if self.payload:
            x, y = self.payload.x + 5, self.payload.y
            dx1, dy1 = self.aim_vector(self.AIM_R)
            dx2, dy2 = self.aim_vector(self.AIM_R + self.power * self.AIM_SIZE)
            x1, y1 = x + dx1, y + dy1
            x2, y2 = x + dx2, y + dy2
            with gl_state():
                # Not sure which bit is being clobbered by this drawing
                # op, but if I don't save it, the sky disappears when on
                # Windows.
                pyglet.graphics.draw(2, gl.GL_LINES,
                    ('v2f', (x1, y1, x2, y2)),
                    ('c3B', (0, 0, 0, 0, 0, 0)),
                )

    def move_left(self):
        self.x = max(self.game.current_level.left + self.MARGIN_LEFT, self.x - 15)

    def move_right(self):
        self.x = min(self.game.current_level.right - self.MARGIN_RIGHT, self.x + 15)

    def aim_up(self):
        self.aim_angle = min(self.aim_angle + 1, self.max_aim_angle)

    def aim_down(self):
        self.aim_angle = max(self.aim_angle - 1, self.min_aim_angle)

    def aim_vector(self, length):
        rad_angle = math.radians(self.aim_angle)
        return length * math.cos(rad_angle), length * math.sin(rad_angle)

    def try_load(self):
        if not self.armed:
            return
        if self.payload:
            # let's unload
            self.payload.y -= self.PAYLOAD_POS[1]
            self.payload = None
            self.set_sprite(self.armed_sprite)
            return
        for dodo in self.game.dodos:
            if (self.x + self.PICKUP_RANGE[0] <= dodo.x <= self.x + self.PICKUP_RANGE[1]
                and not dodo.in_flight and dodo.is_alive):
                self.payload = dodo
                self.payload.sprite = self.payload.ready_sprite
                self.x = self.x # trigger payload placement
                self.y = self.y # trigger payload placement
                self.set_sprite(self.loaded_sprite)
                break


class Level(object):

    def __init__(self, number, left, right, height, next=None):
        self.number = number
        self.left = left
        self.right = right
        self.height = height
        self.next = next


class Map(object):

    GRASS_HEIGHT = 10

    def __init__(self, game):
        self.game = game
        self.text = read_asset('map.txt').rstrip()
        self.lines = self.text.splitlines()[::-1]

        self.tile_width = 100
        self.tile_height = 100

        self.map_width = max(map(len, self.lines)) * self.tile_width

        self.texture = pyglet.image.TextureGrid(
                        pyglet.image.ImageGrid(load_image('map.png'), 3, 1))
        self.images = {'#': load_image('Earth_1.png'),
                       '_': self.texture[1],
                       ' ': self.texture[2]}
        self.background_batch = pyglet.graphics.Batch()
        self.sprites = []
        for map_y, (line, next_line) in enumerate(zip(self.lines, self.lines[1:])):
            for map_x, slot in enumerate(line):
                image = self.images[slot]
                if slot == '#' and (len(next_line) <= map_x or next_line[map_x] == ' '):
                    image = self.images['_']
                s = pyglet.sprite.Sprite(image,
                                         map_x * 100, map_y * 100,
                                         batch=self.background_batch)
                # we need to keep these objects alive, or they're GCed
                self.sprites.append(s)

        self.levels = []
        x1 = 0
        while True:
            x2 = self.vertical_wall_right_of(x1)
            if x2 == x1:
                break
            ground = self.ground_level((x1 + x2) / 2)
            if ground > 0:
                self.levels.append(Level(len(self.levels) + 1, x1, x2, ground))
                log.debug('Level %d: %.1f--%.1f, ground %.1f',
                          len(self.levels), x1, x2, ground)
                if len(self.levels) >= 2:
                    self.levels[-2].next = self.levels[-1]
            x1 = x2

    def draw(self):
        with gl_matrix():
            gl.glTranslatef(self.game.camera.x * -1, self.game.camera.y * -1, 0)
            self.background_batch.draw()

    def vertical_wall_left_of(self, x):
        col = int(x / self.tile_width)
        ground = self.ground_level(x)
        while x > 0 and self.ground_level(x) >= ground:
            col -= 1
            x -= self.tile_width
        return (col + 1) * self.tile_width

    def vertical_wall_right_of(self, x):
        col = int(x / self.tile_width) + 1
        ground = self.ground_level(x)
        while x < self.map_width and self.ground_level(x) <= ground:
            col += 1
            x += self.tile_width
        return (col - 1) * self.tile_width

    def ground_level(self, x):
        col = int(x / self.tile_width)
        y = 0
        for line in self.lines:
            if line[col:col+1].isspace():
                break
            y += self.tile_height
        return y


class Camera(object):

    def __init__(self, game):
        self.game = game
        self.x = 0
        self.y = self.game.game_map.ground_level(0) - 230
        self.target_x = self.x
        self.target_y = self.y

    @property
    def center_x(self):
        return int(self.target_x + window.width // 2)

    @property
    def center_y(self):
        return int(self.target_y + window.height // 2)

    @center_x.setter
    def center_x(self, x):
        self.target_x = int(x - window.height // 2)

    @center_y.setter
    def center_y(self, y):
        self.target_y = int(y - window.height // 2)

    @property
    def bottom_third_y(self):
        return int(self.target_y + window.height // 3)

    @bottom_third_y.setter
    def bottom_third_y(self, y):
        self.target_y = int(y - window.height // 3)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @x.setter
    def x(self, x):
        self._x = max(0, x)

    @y.setter
    def y(self, y):
        self._y = max(0, y)

    def update(self, dt):
        self.x = int(self.x - (self.x - self.target_x) * 0.1)
        self.y = int(self.y - (self.y - self.target_y) * 0.1)
        for dodo in self.game.dodos:
            if dodo.in_flight:
                self.center_x, self.center_y = dodo.x, dodo.y
                return
        self.center_x, self.bottom_third_y = self.game.dodopult.x, self.game.dodopult.y


@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        game.dodopult.move_left()
    elif motion == key.RIGHT:
        game.dodopult.move_right()
    elif motion == key.UP:
        game.dodopult.aim_up()
    elif motion == key.DOWN:
        game.dodopult.aim_down()


@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.SPACE:
        game.dodopult.start_powering_up()
    if symbol in (key.LALT, key.RALT, key.Z):
        game.dodopult.try_load()
    if symbol == key.PLUS:
        game.sea.level += 10


@window.event
def on_key_release(symbol, modifiers):
    if symbol == key.SPACE:
        game.dodopult.fire()


class Sky(object):

    def __init__(self, game):
        self.game = game
        self.background = load_image('sky.png')
        gl.glClearColor(0xd / 255., 0x5d / 255., 0x93 / 255., 1.0)

    def draw(self):
        with gl_matrix():
            gl.glLoadIdentity()
            gl.glTranslatef(0, self.game.camera.y * -0.5, 0)
            with gl_state():
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
                self.background.blit(-100, -300, height=1600, width=window.width+200)


class Sea(object):

    def __init__(self, game):
        self.game = game
        self.batch = pyglet.graphics.Batch()
        self.image = image = load_image('zea.png')
        self.first_layer = []
        self.level = 250
        for x in xrange(0, self.game.game_map.map_width, image.width):
            s = pyglet.sprite.Sprite(image, x, 0,
                                     batch=self.batch)
            self.first_layer.append(s)
        self.phase = 0

    def draw(self):
        x = -75
        y = self.level - self.image.height // 3
        radius_iter = itertools.cycle([-10, 15, -20, 15])
        phase_iter = itertools.cycle([0, 1, 0.5, 1.5])
        phase_mult_iter = itertools.cycle([1.2, 1, 1.1, 1.4, 1.5, 1.6, 1.3])
        phase = 0
        while y > self.game.camera.y - 100:
            radius = radius_iter.next()
            radius_x = radius * 2
            radius_y = radius * 0.5
            phase = phase * 0.5 + (self.phase + math.pi * phase_iter.next()) / phase_mult_iter.next()
            with gl_matrix():
                gl.glTranslatef(int(x + math.sin(phase) * radius_x),
                                int(y + math.cos(phase) * radius_y),
                                0)
                self.batch.draw()
            y -= 20

    def update(self, dt):
        self.phase += dt * 3
        self.level += dt * 1.414 ** (self.game.current_level.number - 1)
        if self.game.dodopult.y < self.level:
            self.game.dodopult.y = self.level
        if self.level >= self.game.current_level.height:
            self.game.next_level()


window.push_handlers(pyglet.window.event.WindowEventLogger())


class Game(object):

    dodo_sprite = load_image('Dodo.png')
    dodo_ready_sprite = load_image('Dodo_ready_for_launch.png')
    dead_dodo_sprite = load_image('deado.png')

    INITIAL_DODOS = 20

    def __init__(self):
        self.game_map = Map(self)

        self.current_level = lvl = self.game_map.levels[0]

        x1 = lvl.left + 20
        x2 = lvl.right - Dodopult.MARGIN_RIGHT
        ground = lvl.height

        self.dodopult = Dodopult(self)
        self.dodopult.x = random.randrange(x1, x2)
        self.dodopult.y = ground
        pyglet.clock.schedule_interval(self.dodopult.update, 0.1)

        self.sea = Sea(self)
        self.sky = Sky(self)
        pyglet.clock.schedule_interval(self.sea.update, 1 / 60.0)

        self.dodos = []
        for dodo in range(self.INITIAL_DODOS):
            dodo = Dodo(self)
            dodo.x = random.randrange(x1, x2)
            dodo.y = ground
            pyglet.clock.schedule_interval(dodo.update, 1 / 60.0)
            self.dodos.append(dodo)

        self.camera = Camera(self)
        pyglet.clock.schedule_interval(self.camera.update, 1 / 60.0)

    def next_level(self):
        for dodo in self.dodos:
            if dodo.is_alive and dodo.y < self.sea.level:
                dodo.go_extinct()
        if self.current_level.next is None:
            log.debug("Game over")
        else:
            self.current_level = self.current_level.next
            x1 = self.current_level.left + 20
            x2 = self.current_level.right - Dodopult.MARGIN_RIGHT
            self.dodopult.x = random.randrange(x1, x2)
            self.dodopult.y = self.current_level.height

    def draw(self):
        self.sky.draw()
        self.game_map.draw()
        with gl_matrix():
            gl.glTranslatef(self.camera.x * -1, self.camera.y * -1, 0)
            for dodo in self.dodos:
                dodo.draw()
            self.dodopult.draw()
            self.sea.draw()


game = Game()


fps_display = pyglet.clock.ClockDisplay()
fps_display.label.y = window.height - 50
fps_display.label.x = window.width - 170


@window.event
def on_draw():
    window.clear()
    game.draw()
    fps_display.draw()


def main():
    pyglet.app.run()


if __name__ == '__main__':
    main()

