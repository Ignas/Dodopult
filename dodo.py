#!/usr/bin/env python
import pyglet
from pyglet.window import key

window = pyglet.window.Window(width=1024, height=786)
font = dict(font_name='Andale Mono',
            font_size=20)


me_text = pyglet.text.document.UnformattedDocument('\n\nu--@')
me_text.set_style(0, len(me_text.text), {
            'font_name': 'Andale Mono',
            'font_size': 20,
            'color': (255, 255, 255, 255)
        })

me = pyglet.text.layout.TextLayout(me_text, 200, 200, multiline=True)
me.x = 500
me.y = 400

window.push_handlers(pyglet.window.event.WindowEventLogger())


@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        me.x -= 16
    elif motion == key.RIGHT:
        me.x += 16

@window.event
def on_key_press(symbol, modifiers):
     if symbol == key.SPACE:
        me_text.text = '\n'.join(['   c',
                                  '   |',
                                  '   @'])

fps_display = pyglet.clock.ClockDisplay()

@window.event
def on_draw():
    window.clear()
    fps_display.draw()
    me.draw()


def main():
    pyglet.app.run()


if __name__ == '__main__':
    main()
