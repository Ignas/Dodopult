#!/usr/bin/env python
import pyglet
import random
from pyglet.window import key

window = pyglet.window.Window(width=1024, height=600)
font = dict(font_name='Andale Mono',
            font_size=20)

class Dodo(object):

    def __init__(self):
        self.label = pyglet.text.Label('.', **font)
        self.label.x = random.randrange(200, 500)
        self.label.y = 100
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
            self.label.x += self.dx / dt
            self.label.y += self.dy / dt
            self.dy -= self.gravity / dt
            if self.label.y < 100:
                self.label.y = 100
                self.dx = self.dy = 0


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

    def __init__(self):
        doc = pyglet.text.document.UnformattedDocument(self.armed_sprite)
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 20,
                    'color': (255, 255, 255, 255)
                })
        self.text = pyglet.text.layout.TextLayout(doc, 200, 200,
                                                  multiline=True)
        self.text.anchor_x = 'left'
        self.text.anchor_y = 'top'
        self.payload = None
        self.armed = True
        self.text.x = 500
        self.text.y = 200

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
            self.payload.y = y - 70

    reload_delay = 2
    time_loading = 0

    def set_sprite(self, sprite):
        self.text.document.text = sprite

    def update(self, dt):
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
                self.payload.launch(5, 10)
            self.armed = False
            self.payload = None
            self.set_sprite(self.unarmed_sprite)

    def draw(self):
        self.text.draw()

    def try_load(self):
        if self.payload or not self.armed:
            return
        for dodo in dodos: # global state :/
            if self.text.x - 10 <= dodo.x <= self.text.x + 20:
                self.payload = dodo
                self.x = self.x # trigger payload placement
                self.y = self.y # trigger payload placement
                self.set_sprite(self.loaded_sprite)
                break


class Map(object):

    def __init__(self):
        self.lines = reversed(open('map.txt').readlines())

    def draw(self):
        pass



game_map = Map()
dodopult = Dodopult()


window.push_handlers(pyglet.window.event.WindowEventLogger())


@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        dodopult.x -= 16
    elif motion == key.RIGHT:
        dodopult.x += 16

@window.event
def on_key_press(symbol, modifiers):
     if symbol == key.SPACE:
         dodopult.fire()
     if symbol in (key.LALT, key.RALT):
         dodopult.try_load()


pyglet.clock.schedule_interval(dodopult.update, 0.1)


fps_display = pyglet.clock.ClockDisplay()

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
