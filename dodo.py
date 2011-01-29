import pyglet
from pyglet.window import key

window = pyglet.window.Window(width=1024, height=786)
font = dict(font_name='Andale Mono',
            font_size=20)

me = pyglet.text.Label('@', x=400, y=300, **font)
me.height = 20
me.width = 16


window.push_handlers(pyglet.window.event.WindowEventLogger())

@window.event
def on_text_motion(motion):
    if motion == key.LEFT:
        me.x -= me.width
    elif motion == key.RIGHT:
        me.x += me.width


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
