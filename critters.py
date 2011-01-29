import random
import math
import logging

import pyglet

log = logging.getLogger('dodo')


class Dodo(object):

    def __init__(self, game):
        self.game = game
        self.sprite = pyglet.sprite.Sprite(pyglet.image.load('dodo.png'))
        self.dead_sprite = pyglet.sprite.Sprite(pyglet.image.load('deado.png'))
        self.dead_sprite.image.anchor_x = 19
        self.x = random.randrange(200, 500)
        self.y = self.game.game_map.ground_level(self.sprite.x)
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

    gravity = 200.0

    def launch(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def go_extinct(self):
        self.dead_sprite.x = self.x
        self.dead_sprite.y = self.y
        self.sprite = self.dead_sprite
        self.is_alive = False

    def update(self, dt):
        if self.dx:
            dx, dy = self.dx * dt, self.dy * dt
            self.x += dx
            self.y += dy
            ground_level = self.game.game_map.ground_level(self.x)
            if self.y < ground_level:
                log.debug('collision: (%.1f, %.1f) + (%+.1f, %.1f) -> (%.1f, %.1f)',
                          self.x - dx, self.y - dy, dx, dy, self.x, self.y)
                log.debug('ground level at %.1f: %.1f', self.x, ground_level)
                # scale (dx, dy) -> (ndx, ndy) so old_y + ndy == ground_level
                ndy = ground_level - self.y + dy
                ndx = ndy * dx / dy
                log.debug('clip #1: (%+.1f, %+.1f)', ndx, ndy)
                # but what if we hit a vertical wall?
                old_ground_level = self.game.game_map.ground_level(self.x - dx)
                if ground_level > old_ground_level:
                    wall_x = self.game.game_map.vertical_wall_left_of(self.x)
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
                self.dx *= 0.98

