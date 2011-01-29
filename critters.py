import random
import logging

import pyglet


log = logging.getLogger('dodo')


class Dodo(object):

    SPRITE_SCALE = 0.7

    def __init__(self, game):
        self.game = game
        self.standing_sprite = pyglet.sprite.Sprite(game.dodo_sprite)
        self.standing_sprite.scale = self.SPRITE_SCALE
        self.standing_sprite.image.anchor_y = 12 + random.randint(-1, 1)
        self.ready_sprite = pyglet.sprite.Sprite(game.dodo_ready_sprite)
        self.ready_sprite.scale = self.SPRITE_SCALE
        self.ready_sprite.image.anchor_x = 17
        self.ready_sprite.image.anchor_y = 13
        self.dead_sprite = pyglet.sprite.Sprite(game.dead_dodo_sprite)
        self.dead_sprite.image.anchor_x = 19
        self.sprite = self.standing_sprite
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

    def survive(self):
        self.standing_sprite.x = self.x
        self.standing_sprite.y = self.y
        self.sprite = self.standing_sprite

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
                else:
                    self.x = x1
                    self.y = y1
                    self.survive()
                self.dx = self.dy = 0
            else:
                self.dy -= self.gravity * dt
                self.dx *= (1 - 0.007)

