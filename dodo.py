#!/usr/bin/env python
import random
import math
import pyglet
from pyglet.window import key


window = pyglet.window.Window(width=1024, height=600)
font = dict(font_name='Andale Mono',
            font_size=20)



class Dodo(object):

    def __init__(self):
        self.label = pyglet.text.Label('.', **font)
        self.label.x = random.randrange(200, 500)
        self.label.y = game_map.ground_level(self.label.x)
        self.dx = 0
        self.dy = 0

    def draw(self):
        self.label.draw()

    @property
    def x(self):
        return self.label.x

    @x.setter
    def x(self, x):
        self.label.x = x

    @property
    def y(self):
        return self.label.y

    @y.setter
    def y(self, y):
        self.label.y = y

    gravity = 0.2

    def launch(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def update(self, dt):
        if self.dx:
            dx, dy = self.dx / dt, self.dy / dt
            self.label.x += dx
            self.label.y += dy
            ground_level = game_map.ground_level(self.label.x)
            if self.label.y < ground_level:
                # scale (dx, dy) -> (ndx, ndy) so old_y + ndy == ground_level
                ndy = ground_level - self.label.y + dy
                ndx = ndy * dx / dy
                # but what if we hit a vertical wall?
                old_ground_level = game_map.ground_level(self.label.x - dx)
                if ground_level > old_ground_level:
                    wall_x = game_map.vertical_wall_left_of(self.label.x) - 7
                    # scale (dx, dy) -> (ndx2, ndy2) so old_x + ndx = wall_x
                    ndx2 = wall_x - self.label.x + dx
                    ndy2 = ndx2 * dy / dx
                    # now see which vector is shorter
                    if math.hypot(ndx2, ndy2) < math.hypot(ndx, ndy):
                        ndx, ndy = ndx2, ndy2
                self.label.x += ndx - dx
                self.label.y += ndy - dy
                self.dx = self.dy = 0
            else:
                self.dy -= self.gravity / dt


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
                    'color': (255, 255, 255, 255)
                })
        self.text = pyglet.text.layout.TextLayout(doc, 100, 100,
                                                  multiline=True)
        self.text.anchor_x = 'left'
        self.text.anchor_y = 'bottom'
        self.payload = None
        self.armed = True
        self.text.x = 500
        self.text.y = game_map.ground_level(self.text.x)

        doc = pyglet.text.document.UnformattedDocument('*\n' * (self.power + 1))
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 20,
                    'line_spacing': 12,
                    'color': (255, 255, 255, 255)
                })
        self.power_bar = pyglet.text.layout.TextLayout(doc, 100, 800,
                                                       multiline=True)
        self.power_bar.anchor_y = 'top'
        self.power_bar.x = window.width - 20
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
    power = 0
    max_power = 20.0

    def set_sprite(self, sprite):
        self.text.document.text = sprite

    def update(self, dt):
        self.power_bar.document.text = ' \n' * int(self.max_power - self.power) +  '*\n' * (self.power + 1)
        if self.powering_up:
            self.power = min(self.power + 1, self.max_power)
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
                self.payload.launch(*self.aim_vector(self.power / self.max_power))
            self.power = 0
            self.powering_up = False
            self.armed = False
            self.payload = None
            self.set_sprite(self.unarmed_sprite)

    def start_powering_up(self):
        if self.armed:
            self.powering_up = True

    def draw(self):
        self.power_bar.draw()
        self.text.draw()

    aim_angle = 30
    min_aim_angle = 15
    max_aim_angle = 75
    power_step = 20.0

    def aim_up(self):
        self.aim_angle == min(self.aim_angle + 1, self.max_aim_angle)

    def aim_down(self):
        self.aim_angle == max(self.aim_angle - 1, self.min_aim_angle)

    def aim_vector(self, power_percentage):
        import math
        rad_angle = math.pi * (self.aim_angle / 180.0)
        power = self.power_step * power_percentage
        return power * math.cos(rad_angle), power * math.sin(rad_angle)

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
        doc = pyglet.text.document.UnformattedDocument(self.text)
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 50,
                    'color': (255, 255, 255, 128)
                })
        self.text = pyglet.text.layout.TextLayout(doc, 5000, 5000, multiline=True)
        self.text.height = self.text.content_height
        self.text.anchor_x, self.text.anchor_y = 'left', 'bottom'
        self.tile_width = self.text.content_width / max(map(len, self.lines))
        self.tile_height = self.text.content_height / len(self.lines)

    def find_this_level(self, target_level):
        current_level = -1
        for n, line in enumerate(self.lines):
            if '_' in line:
                current_level += 1
            if current_level == target_level:
                return n

    def draw(self):
        self.text.draw()

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


window.push_handlers(pyglet.window.event.WindowEventLogger())


@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        dodopult.x -= 16
    elif motion == key.RIGHT:
        dodopult.x += 16
    elif motion == key.UP:
        dodopult.aim_up()
    elif motion == key.DOWN:
        dodopult.aim_down()


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
fps_display.label.y = 550
fps_display.label.x = 850

dodos = [Dodo() for n in range(5)]

for dodo in dodos:
    pyglet.clock.schedule_interval(dodo.update, 0.1)


@window.event
def on_draw():
    window.clear()
    fps_display.draw()
    for dodo in dodos:
        dodo.draw()
    dodopult.draw()
    game_map.draw()


def main():
    pyglet.app.run()


if __name__ == '__main__':
    main()
