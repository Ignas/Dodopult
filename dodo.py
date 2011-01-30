#!/usr/bin/env python
import math
import os.path
import random
import logging
import itertools
from contextlib import contextmanager

import pyglet
from pyglet.window import key
from pyglet import gl


log = logging.getLogger('dodo')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


pyglet.resource.path = ['assets', 'assets/sounds']
pyglet.resource.reindex()


def load_image(filename):
    return pyglet.resource.image(filename)


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


class Dodo(object):

    thud = pyglet.resource.media('thud.wav', streaming=False)

    standing_image = load_image('Dodo.png')
    standing_image.anchor_y = 12

    ready_image = load_image('Dodo_ready_for_launch.png')
    ready_image.anchor_x = 17
    ready_image.anchor_y = 13

    dead_image = load_image('Dodo_broken.png')
    dead_image.anchor_x = -10

    SPRITE_SCALE = 0.7

    def __init__(self, game):
        self.game = game
        self.sprite = pyglet.sprite.Sprite(self.standing_image,
                                           batch=game.dodo_batch)
        self.sprite.scale = self.SPRITE_SCALE
        self.dx = 0
        self.dy = 0
        self.is_alive = True

    def draw(self):
        self.sprite.draw()

    @property
    def in_flight(self):
        return self.dx != 0 or self.dy != 0

    @property
    def x(self):
        return self.sprite.x

    @x.setter
    def x(self, x):
        self.sprite.x = x

    @property
    def y(self):
        return self.sprite.y

    @y.setter
    def y(self, y):
        self.sprite.y = y

    def launch(self, dx, dy):
        self.dx = dx
        self.dy = dy
        self.game.camera.focus_on(self)

    def go_extinct(self):
        self.sprite.image = self.dead_image
        self.is_alive = False
        self.game.camera.remove_focus(self)

    def survive(self):
        if self.is_alive:
            self.sprite.image = self.standing_image
        self.game.camera.remove_focus(self)

    def update(self, dt):
        dt = dt * 3
        if self.dx or self.dy:
            dx, dy = self.dx * dt, self.dy * dt
            self.x += dx
            self.y += dy
            ground_level = self.game.game_map.ground_level(self.x)
            if self.y < ground_level:
                log.debug('collision: (%.1f, %.1f) + (%+.1f, %.1f) -> (%.1f, %.1f)',
                          self.x - dx, self.y - dy, dx, dy, self.x, self.y)
                log.debug('ground level at %.1f: %.1f', self.x, ground_level)
                wall_x = self.game.game_map.vertical_wall_left_of(self.x)
                log.debug('wall at %.1f', wall_x)
                if wall_x < self.x - dx:
                    log.debug('inside the wall!')
                    wall_x = self.x - dx

                if self.y - dy >= ground_level:
                    # we hit the ground from above
                    x1 = self.x - dx + (ground_level - self.y + dy) * dx / dy
                    y1 = ground_level
                    log.debug('clip against ground: (%.1f, %.1f)', x1, y1)
                else:
                    x1 = y1 = None

                if self.x - dx <= wall_x:
                    # we hit a wall from the left
                    # scale (dx, dy) -> (ndx2, ndy2) so old_x + ndx = wall_x
                    y2 = self.y - dy + (wall_x - self.x + dx) * dy / dx
                    x2 = wall_x
                    log.debug('clip against wall: (%.1f, %.1f)', x2, y2)
                    if y2 > ground_level:
                        log.debug('wall clip above ground')
                        x2 = y2 = None
                    if x1 is not None and x1 < wall_x:
                        log.debug('ground clip left of cliff')
                        x1 = y1 = None
                else:
                    x2 = y2 = None

                if x1 is None:
                    log.debug('wall wins')
                    self.x = x2
                    self.y = y2
                    self.go_extinct()
                    player = pyglet.media.Player()
                    player.queue(self.thud)
                    player.seek(1)
                    player.play()
                else:
                    self.x = x1
                    self.y = y1
                    self.survive()
                self.dx = self.dy = 0
                self.game.count_surviving_dodos()
            else:
                self.dy -= self.game.gravity * dt
                self.dx *= (1 - self.game.air_resistance)


class PowerBar(object):

    steps = 7

    def __init__(self, dodopult):
        self.dodopult = dodopult

        self.textures = pyglet.image.TextureGrid(
                            pyglet.image.ImageGrid(
                                load_image('power_bar.png'),
                                self.steps, 1))
        self.power_bar = pyglet.sprite.Sprite(self.textures[0], 20, 20)

    def draw(self):
        if not self.dodopult.payload:
            return

        range = float(self.dodopult.max_power - self.dodopult.min_power)
        power = (self.dodopult.power - self.dodopult.min_power) / range
        n = self.steps - int(power * (self.steps - 1)) - 1
        self.power_bar.image = self.textures[n]
        self.power_bar.rotation = -self.dodopult.aim_angle

        x = self.dodopult.payload.x + 5
        y = self.dodopult.payload.y
        dx, dy = self.dodopult.aim_vector(self.dodopult.AIM_R)
        self.power_bar.set_position(x + dx, y + dy)
        self.power_bar.draw()


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

    MARGIN_LEFT = -40
    MARGIN_RIGHT = 110

    AIM_R = 50
    AIM_SIZE = 0.15

    INITIAL_X = 500

    VERT_ADJUST = 7

    min_power = 200.0         # pixels per second
    max_power = 1000.0        # pixels per second
    power_increase = 400.0    # pixels per second per second

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
        return self.sprite.y + self.VERT_ADJUST

    @y.setter
    def y(self, y):
        self.sprite.y = y - self.VERT_ADJUST
        if self.payload:
            self.payload.y = y + self.PAYLOAD_POS[1] - self.VERT_ADJUST

    def set_sprite(self, sprite):
        self.sprite.image = sprite

    def update(self, dt):
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
        self.sprite.draw()

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
                dodo.sprite.image = dodo.ready_image
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

    def random_x(self):
        x1 = min(self.left, self.right)
        x2 = max(x1, self.right - Dodopult.MARGIN_RIGHT)
        return random.randint(x1, x2)

    def place(self, obj):
        obj.x = self.random_x()
        obj.y = self.height


class Map(object):

    solid = load_image('Earth_1.png')
    grass_on_top = load_image('Earth_2.png')
    cliff_on_left = load_image('Earth_3_side.png')
    cliff_on_left_and_grass_on_top = load_image('Earth_4_side_corner.png')
    inner_cliff_corner = load_image('Earth_5_inner_corner.png')

    GRASS_HEIGHT = 10

    def __init__(self, game):
        self.game = game
        self.text = pyglet.resource.file('map.txt').read().rstrip()
        self.lines = self.text.splitlines()[::-1]

        self.tile_width = 100
        self.tile_height = 100

        self.map_width = max(map(len, self.lines)) * self.tile_width
        self.map_height = len(self.lines) * self.tile_height

        self.background_batch = pyglet.graphics.Batch()
        self.sprites = []
        for map_y, line in enumerate(self.lines):
            try:
                above = self.lines[map_y + 1]
            except IndexError:
                above = ''
            for map_x, slot in enumerate(line):
                if slot == ' ':
                    continue

                air_above = map_x >= len(above) or above[map_x] == ' '
                air_to_the_left = map_x > 0 and line[map_x - 1] == ' '
                air_above_to_the_left = (map_x - 1 >= len(above)
                                         or map_x == 0
                                         or above[map_x - 1] == ' ')

                if air_above and air_to_the_left:
                    image = self.cliff_on_left_and_grass_on_top
                elif air_above:
                    image = self.grass_on_top
                elif air_to_the_left:
                    image = self.cliff_on_left
                elif air_above_to_the_left:
                    image = self.inner_cliff_corner
                else:
                    image = self.solid

                s = pyglet.sprite.Sprite(image,
                                         map_x * self.tile_width,
                                         map_y * self.tile_height,
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
        self.focus = None
        self.focus_timer = 0

    @property
    def center_x(self):
        return int(self.target_x + window.width // 2)

    @property
    def center_y(self):
        return int(self.target_y + window.height // 2)

    @center_x.setter
    def center_x(self, x):
        self.target_x = int(x - window.width // 2)

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

    def focus_on(self, obj):
        self.focus = obj
        self.focus_timer = 0

    def remove_focus(self, obj):
        if self.focus is obj:
            self.focus_timer = 1.5 # seconds

    def update(self, dt):
        self.x = int(self.x - (self.x - self.target_x) * 0.1)
        self.y = int(self.y - (self.y - self.target_y) * 0.1)
        if self.focus:
            self.center_x, self.center_y = self.focus.x, self.focus.y
            if self.focus_timer > 0:
                self.focus_timer -= dt
                if self.focus_timer <= 0:
                    self.focus_on(None)
        else:
            self.center_x, self.bottom_third_y = self.game.dodopult.x, self.game.dodopult.y


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


class Clouds(object):

    images = ([load_image('Cloud_1.png')] * 10 +
              [load_image('Cloud_2.png')] + # rainbows are rare
              [load_image('Cloud_3.png')] * 10)

    parallax = -0.5
    density = 1 / 200000. # 1 cloud in square mm

    def __init__(self, game):
        self.game = game
        self.batch = pyglet.graphics.Batch()
        self.sprites = []
        map = game.game_map
        n = map.map_width * map.map_height * self.parallax ** 2 * self.density
        for i in range(int(n)):
            x = random.uniform(0, map.map_width * abs(self.parallax))
            y = random.uniform(0, map.map_height * abs(self.parallax))
            s = pyglet.sprite.Sprite(random.choice(self.images), x, y,
                                     batch=self.batch)
            self.sprites.append(s)

    def draw(self):
        with gl_matrix():
            gl.glTranslatef(self.game.camera.x * self.parallax,
                            self.game.camera.y * self.parallax, 0)
            self.batch.draw()


class Sea(object):

    def __init__(self, game):
        self.game = game
        self.batch = pyglet.graphics.Batch()
        self.image = image = load_image('Wave.png')
        self.first_layer = []
        self.level = 250

        max_throw_distance = game.dodopult.max_power ** 2 / game.gravity
        w = self.game.game_map.map_width + window.width + max_throw_distance

        for x in xrange(0, int(w), image.width):
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



class Game(object):

    gravity = 200.0 # pixels per second squared
    air_resistance = 0.007 # i.e. a loss of 0.7% per seco^W per update
                           # XXX fix this to be per second

    game_over_animation = 5.0 # seconds

    update_freq = 1 / 60.

    INITIAL_DODOS = 20

    def __init__(self):
        self.game_map = Map(self)
        self.current_level = self.game_map.levels[0]
        self.game_is_over = False
        self.game_over_time = 0

        self.dodopult = Dodopult(self)
        self.current_level.place(self.dodopult)
        pyglet.clock.schedule_interval(self.dodopult.update, self.update_freq)

        self.powerbar = PowerBar(self.dodopult)

        self.sea = Sea(self)
        pyglet.clock.schedule_interval(self.sea.update, self.update_freq)

        self.sky = Sky(self)
        self.clouds = Clouds(self)

        self.dodos = []
        self.dodo_batch = pyglet.graphics.Batch()
        for dodo in range(self.INITIAL_DODOS):
            self.add_dodo()

        self.camera = Camera(self)
        pyglet.clock.schedule_interval(self.camera.update, self.update_freq)

        pyglet.clock.schedule_interval(self.update, self.update_freq)

    def add_dodo(self):
        dodo = Dodo(self)
        self.current_level.place(dodo)
        pyglet.clock.schedule_interval(dodo.update, self.update_freq)
        self.dodos.append(dodo)

    def count_surviving_dodos(self):
        above = 0
        here = 0
        for dodo in self.dodos:
            if dodo.is_alive:
                if dodo.y > self.current_level.height:
                    above += 1
                elif dodo.y == self.current_level.height:
                    here += 1
        if here == 0 and above > 0:
            log.debug("Going to next level with %d live dodos", above)
            self.next_level()

    def next_level(self):
        for dodo in self.dodos:
            if dodo.is_alive and dodo.y < self.sea.level:
                dodo.go_extinct()
        if (self.current_level.next is None or
            self.current_level.next.next is None):
            self.game_over()
        else:
            self.current_level = self.current_level.next
            self.current_level.place(self.dodopult)

    def game_over(self):
        log.debug("Game over")
        bunny = Dodo(self)
        lvl = self.game_map.levels[-1]
        bunny.x = (lvl.left + lvl.right) / 2 + self.game_map.tile_width * 1.5
        bunny.y = lvl.height - self.game_map.tile_height * 7
        self.camera.focus_on(bunny)
        self.game_is_over = True

    def update(self, dt):
        if self.game_is_over:
            self.game_over_time = min(self.game_over_animation,
                                      self.game_over_time + dt)

    def draw(self):
        with gl_matrix():
            if self.game_is_over:
                t = self.game_over_time / self.game_over_animation
                scale = 1 - t * (1 - 1/5.)
                gl.glTranslatef(window.width / 2, window.height // 2, 0)
                gl.glScalef(scale, scale, 1.0)
                gl.glTranslatef(-window.width / 2, -window.height // 2, 0)
            self.sky.draw()
            self.clouds.draw()
            self.game_map.draw()
            with gl_matrix():
                gl.glTranslatef(self.camera.x * -1, self.camera.y * -1, 0)
                self.dodo_batch.draw()
                self.dodopult.draw()
                self.sea.draw()
                self.powerbar.draw()


class Main(object):

    fps_display = None

    def __init__(self):
        self.game = Game()

        window.event(self.on_draw)
        window.event(self.on_text_motion)
        window.event(self.on_key_press)
        window.event(self.on_key_release)
        window.event(self.on_resize)

        self.fps_display = pyglet.clock.ClockDisplay()
        self.fps_display.label.y = window.height - 50
        self.fps_display.label.x = window.width - 170

    def on_draw(self):
        window.clear()
        self.game.draw()
        if self.fps_display:
            self.fps_display.draw()

    def on_text_motion(self, motion):
        if motion == key.LEFT:
            self.game.dodopult.move_left()
        elif motion == key.RIGHT:
            self.game.dodopult.move_right()
        elif motion == key.UP:
            self.game.dodopult.aim_up()
        elif motion == key.DOWN:
            self.game.dodopult.aim_down()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.game.dodopult.start_powering_up()
        if symbol in (key.LALT, key.RALT, key.Z):
            self.game.dodopult.try_load()
        if symbol == key.F:
            window.set_fullscreen(not window.fullscreen)
        # DEBUG/CHEAT CODES
        if symbol == key.ASCIITILDE:
            g = self.game
            g.sea.level = max(g.sea.level + 10,
                              g.current_level.height - window.height // 2)
        if symbol == key.SLASH:
            # Note: leaves update() methods running, which maybe ain't bad
            # -- eradicating a dodo mid-flight won't leave the camera focus
            # stuck on it then
            for dodo in self.game.dodos[::2]:
                dodo.sprite.visible = False
            del self.game.dodos[::2]
        if symbol == key.PLUS:
            self.game.add_dodo()
        if symbol == key.N:
            if (self.game.current_level.next is not None and
                self.game.current_level.next.next is not None):
                self.game.next_level()
        if symbol == key.G:
            self.game.game_over()

    def on_key_release(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.game.dodopult.fire()

    def on_resize(self, width, height):
        if self.fps_display:
            self.fps_display.label.y = window.height - 50
            self.fps_display.label.x = window.width - 170

    def run(self):
        pyglet.app.run()


def main():
    global window
    window = pyglet.window.Window(width=1024, height=600,
                                  resizable=True,
                                  caption='Save the Dodos')
    window.set_minimum_size(320, 200) # does not work on linux with compiz
    window.maximize()
    window.set_mouse_visible(True)
    window.set_icon(pyglet.image.load(os.path.join(pyglet.resource.location('Dodo.png').path,
                                                   'Dodo.png')))
    app = Main()
    app.run()


if __name__ == '__main__':
    main()

