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


class Dodopult(object):

    def __init__(self):
        doc = pyglet.text.document.UnformattedDocument('\n\nu--@')
        doc.set_style(0, len(doc.text), {
                    'font_name': 'Andale Mono',
                    'font_size': 20,
                    'color': (255, 255, 255, 255)
                })
        self.text = pyglet.text.layout.TextLayout(doc, 200, 200, multiline=True)
        self.loaded = True
        self.text.x = 500
        self.text.y = 0

    reload_delay = 2
    time_loading = 0

    def update(self, dt):
        if not self.loaded:
            self.time_loading += dt
            if self.time_loading < self.reload_delay / 3.0:
                pass
            elif self.time_loading < self.reload_delay * 2 / 3.0:
                self.text.document.text = '\n'.join([' c  ',
                                                     '  \ ',
                                                     '   @'])
            elif self.time_loading < self.reload_delay:
                self.text.document.text = '\n'.join(['    ',
                                                     'u-. ',
                                                     '   @'])
            else:
                self.time_loading = 0
                self.loaded = True
                self.text.document.text = '\n\nu--@'

    def fire(self):
        if self.loaded:
            self.loaded = False
            self.text.document.text = '\n'.join(['   c',
                                                 '   |',
                                                 '   @'])

    def draw(self):
        self.text.draw()

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
