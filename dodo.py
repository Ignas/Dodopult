#!/usr/bin/env python
import random
import math
import logging

import pyglet
from pyglet.window import key
from pyglet.gl import glPushMatrix, glPopMatrix, glTranslatef, glLoadIdentity


log = logging.getLogger('dodo')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


window = pyglet.window.Window(width=1024, height=600)
font = dict(font_name='Andale Mono',
            font_size=20,
            color=(0, 0, 0, 255))



class Dodo(object):

    def __init__(self):
        self.sprite = pyglet.sprite.Sprite(pyglet.image.load('dodo.png'))
        self.dead_sprite = pyglet.sprite.Sprite(pyglet.image.load('deado.png'))
        self.dead_sprite.image.anchor_x = 19
        self.x = random.randrange(200, 500)
        self.y = game_map.ground_level(self.sprite.x)
        self.dx = 0
        self.dy = 0

    def draw(self):
        self.sprite.draw()

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

    gravity = 200.0

    def launch(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def go_extinct(self):
        self.dead_sprite.x = self.x
        self.dead_sprite.y = self.y
        self.sprite = self.dead_sprite

    def update(self, dt):
        if self.dx:
            dx, dy = self.dx * dt, self.dy * dt
            self.x += dx
            self.y += dy
            ground_level = game_map.ground_level(self.x)
            if self.y < ground_level:
                log.debug('collision: (%.1f, %.1f) + (%+.1f, %.1f) -> (%.1f, %.1f)',
                          self.x - dx, self.y - dy, dx, dy, self.x, self.y)
                log.debug('ground level at %.1f: %.1f', self.x, ground_level)
                # scale (dx, dy) -> (ndx, ndy) so old_y + ndy == ground_level
                ndy = ground_level - self.y + dy
                ndx = ndy * dx / dy
                log.debug('clip #1: (%+.1f, %+.1f)', ndx, ndy)
                # but what if we hit a vertical wall?
                old_ground_level = game_map.ground_level(self.x - dx)
                if ground_level > old_ground_level:
                    wall_x = game_map.vertical_wall_left_of(self.x)
                    log.debug('wall at %.1f', wall_x)
                    # scale (dx, dy) -> (ndx2, ndy2) so old_x + ndx = wall_x
                    ndx2 = wall_x - self.x + dx
                    ndy2 = ndx2 * dy / dx
                    log.debug('clip #2: (%+.1f, %+.1f)', ndx2, ndy2)
                    # now see which vector is shorter -- XXX bug
                    if math.hypot(ndx2, ndy2) < math.hypot(ndx, ndy):
                        log.debug('clip #2 wins')
                        ndx, ndy = ndx2, ndy2
                        self.go_extinct()
                self.x += ndx - dx
                self.y += ndy - dy
                self.dx = self.dy = 0
            else:
                self.dy -= self.gravity * dt


class Dodopult(object):

    armed_sprite = ('    \n'
                    '    \n'
                    'u--@')

    loaded_sprite = armed_sprite

    unarmed_sprite = ('   c\n'
                      '   |\n'
                      '   @')

    arming_sprite_1 = (' c  \n'
                       '  \ \n'
                       '   @')

    arming_sprite_2 = ('    \n'
                       'u-_ \n'
                       '   @')

    powering_up = False

    def __init__(self):
        doc = pyglet.text.document.UnformattedDocument(self.armed_sprite)
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 20,
                    'color': (0, 0, 0, 255)
                })
        self.text = pyglet.text.layout.TextLayout(doc, 100, 100,
                                                  multiline=True)
        self.text.anchor_x = 'left'
        self.text.anchor_y = 'bottom'
        self.payload = None
        self.armed = True
        self.text.x = 500
        self.text.y = game_map.ground_level(self.text.x)

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
        return self.text.x

    @x.setter
    def x(self, x):
        self.text.x = x
        if self.payload:
            self.payload.x = x

    @property
    def y(self):
        return self.text.y

    @y.setter
    def y(self, y):
        self.text.y = y
        if self.payload:
            self.payload.y = y + 30

    reload_delay = 2
    time_loading = 0
    power = min_power = 500.0
    max_power = 2000.0
    power_increase = 100.0 # pixels per second per second

    def set_sprite(self, sprite):
        self.text.document.text = sprite

    def update(self, dt):
        power = (self.power - self.min_power) / (self.max_power - self.min_power)
        n1 = 1 + int(power * 20)
        n2 = 21 - n1
        self.power_bar.document.text = ' \n' * n2 +  '*\n' * n1
        if self.powering_up:
            self.power = min(self.power + dt * self.power_increase, self.max_power)
        if not self.armed:
            self.time_loading += dt
            if self.time_loading < self.reload_delay / 3.0:
                pass
            elif self.time_loading < self.reload_delay * 2 / 3.0:
                self.set_sprite(self.arming_sprite_1)
            elif self.time_loading < self.reload_delay:
                self.set_sprite(self.arming_sprite_2)
            else:
                self.time_loading = 0
                self.armed = True
                self.set_sprite(self.armed_sprite)

    def fire(self):
        if self.armed:
            if self.payload:
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
        glPushMatrix()
        glLoadIdentity()
        self.power_bar.draw()
        glPopMatrix()
        self.text.draw()
        if self.payload:
            x, y = self.payload.x + 5, self.payload.y
            dx1, dy1 = self.aim_vector(30)
            dx2, dy2 = self.aim_vector(35 + self.power)
            x1, y1 = x + dx1, y + dy1
            x2, y2 = x + dx2, y + dy2
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                ('v2f', (x1, y1, x2, y2)),
                ('c3B', (0, 0, 0, 0, 0, 0)),
            )

    aim_angle = 45
    min_aim_angle = 15
    max_aim_angle = 75

    def move_left(self):
        self.x = max(0, self.x - 15)

    def move_right(self):
        self.x += 15

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
            self.payload.y -= 30
            self.payload = None
            self.set_sprite(self.armed_sprite)
            return
        for dodo in dodos: # global state :/
            if self.text.x - 10 <= dodo.x <= self.text.x + 20:
                self.payload = dodo
                self.x = self.x # trigger payload placement
                self.y = self.y # trigger payload placement
                self.set_sprite(self.loaded_sprite)
                break


class Map(object):

    level = 0

    def __init__(self):
        self.text = open('map.txt').read().rstrip()
        self.lines = self.text.splitlines()[::-1]

        self.tile_width = 40
        self.tile_height = 100

        self.texture = pyglet.image.TextureGrid(pyglet.image.ImageGrid(pyglet.image.load('map.png'), 3, 1))
        self.images = {'#': self.texture[0], '_': self.texture[1], ' ': self.texture[2]}
        self.background_batch = pyglet.graphics.Batch()
        self.sprites = []
        for map_y, line in enumerate(self.lines):
            for map_x, slot in enumerate(line):
                pos = (map_x * 40, map_y * 100)
                image = self.images[slot]
                s = pyglet.sprite.Sprite(image,
                                         map_x * 40, map_y * 100,
                                         batch=self.background_batch)
                self.sprites.append(s)

    def find_this_level(self, target_level):
        current_level = -1
        for n, line in enumerate(self.lines):
            if '_' in line:
                current_level += 1
            if current_level == target_level:
                return n

    background_batch = None

    def draw(self):
        glPushMatrix()
        glTranslatef(camera.x * -1, camera.y * -1, 0)
        self.background_batch.draw()
        glPopMatrix()

    def vertical_wall_left_of(self, x):
        col = int(x / self.tile_width)
        gl = self.ground_level(x)
        while x > 0 and self.ground_level(x) >= gl:
            col -= 1
            x -= self.tile_width
        return (col + 1) * self.tile_width

    def ground_level(self, x):
        col = int(x / self.tile_width)
        y = 0
        for line in self.lines:
            if line[col:col+1] == '_':
                y += 10
                break
            if line[col:col+1].isspace():
                break
            y += self.tile_height
        return y


game_map = Map()

dodopult = Dodopult()


class Camera(object):

    def __init__(self):
        self.x = 0
        self.y = game_map.ground_level(0) - 230

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


camera = Camera()


@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        dodopult.move_left()
    elif motion == key.RIGHT:
        dodopult.move_right()
    elif motion == key.UP:
        dodopult.aim_up()
    elif motion == key.DOWN:
        dodopult.aim_down()


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    camera.x -= dx
    camera.y -= dy


@window.event
def on_mouse_release(x, y, button, modifiers):
    log.debug('camera position: (%.1f, %.1f)', camera.x, camera.y)


@window.event
def on_text(text):
    if text == 'w':
        camera.y += 10
    elif text == 'a':
        camera.x -= 10
    elif text == 's':
        camera.y -= 10
    elif text == 'd':
        camera.x += 10


@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.SPACE:
        dodopult.start_powering_up()
    if symbol in (key.LALT, key.RALT):
        dodopult.try_load()


@window.event
def on_key_release(symbol, modifiers):
    if symbol == key.SPACE:
        dodopult.fire()


pyglet.clock.schedule_interval(dodopult.update, 0.1)


fps_display = pyglet.clock.ClockDisplay()
fps_display.label.y = window.height - 50
fps_display.label.x = window.width - 170


dodos = [Dodo() for n in range(5)]

for dodo in dodos:
    pyglet.clock.schedule_interval(dodo.update, 1 / 25.0)


class Sky(object):

    def __init__(self):
        self.background = pyglet.image.load('sky.png')

    def draw(self):
        glPushMatrix()
        glTranslatef(camera.x * -0.5, camera.y * -0.5, 0)
        self.background.blit(-1000, -300, height=1600, width=2400)
        glPopMatrix()

sky = Sky()


class Sea(object):

    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        image = pyglet.image.load('zea.png')
        self.first_layer = []
        for x in range(20):
            s = pyglet.sprite.Sprite(image,
                                     x * image.width, 0,
                                     batch=self.batch)
            self.first_layer.append(s)

    def draw(self):
        self.batch.draw()
        glPushMatrix()
        glTranslatef(-75, -20, 0)
        self.batch.draw()
        glTranslatef(-75, -20, 0)
        self.batch.draw()
        glPopMatrix()

sea = Sea()

window.push_handlers(pyglet.window.event.WindowEventLogger())

@window.event
def on_draw():
    window.clear()
    sky.draw()
    game_map.draw()
    fps_display.draw()
    glPushMatrix()
    glTranslatef(camera.x * -1, camera.y * -1, 0)
    for dodo in dodos:
        dodo.draw()
    dodopult.draw()
    sea.draw()
    glPopMatrix()


def main():
    pyglet.app.run()


if __name__ == '__main__':
    main()
