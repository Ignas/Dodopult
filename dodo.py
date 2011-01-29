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

    def draw(self):
        self.label.draw()

    @property
    def x(self):
        return self.label.x


class Dodopult(object):

    armed_sprite = ('    \n'
                    '    \n'
                    'u--@')

    loaded_sprite = ('    \n'
                     '    \n'
                    u'\xfb--@')

    unarmed_sprite = ('   c\n'
                      '   |\n'
                      '   @')

    arming_sprite_1 = (' c  \n'
                       '  \ \n'
                       '   @')

    arming_sprite_2 = ('    \n'
                       'u-. \n'
                       '   @')

    def __init__(self):
        doc = pyglet.text.document.UnformattedDocument(self.armed_sprite)
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 20,
                    'color': (255, 255, 255, 255)
                })
        self.text = pyglet.text.layout.TextLayout(doc, 200, 200, multiline=True)
        self.loaded = False
        self.armed = True
        self.text.x = 500
        self.text.y = 0

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
            self.armed = False
            self.loaded = False
            self.set_sprite(self.unarmed_sprite)

    def draw(self):
        self.text.draw()

    def try_load(self):
        if self.loaded or not self.armed:
            return
        for dodo in dodos: # global state :/
            if self.text.x <= dodo.x <= self.text.x + 20:
                self.loaded = True
                self.set_sprite(self.loaded_sprite)


class Map(object):
    pass


dodopult = Dodopult()


window.push_handlers(pyglet.window.event.WindowEventLogger())


@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        dodopult.text.x -= 16
    elif motion == key.RIGHT:
        dodopult.text.x += 16

@window.event
def on_key_press(symbol, modifiers):
     if symbol == key.SPACE:
         dodopult.fire()
     if symbol in (key.LALT, key.RALT):
         dodopult.try_load()


pyglet.clock.schedule_interval(dodopult.update, 0.1)


fps_display = pyglet.clock.ClockDisplay()

dodos = [Dodo() for n in range(5)]

@window.event
def on_draw():
    window.clear()
    fps_display.draw()
    for dodo in dodos:
        dodo.draw()
    dodopult.draw()


def main():
    pyglet.app.run()


if __name__ == '__main__':
    main()
