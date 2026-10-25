import sys
import random
import math

import pygame

class Emitter:
    def __init__(self, game, pos, velocity, angle, velocity_decrease=1):
        self.game = game
        self.pos = list(pos)
        self.velocity = velocity
        self.angle = angle
        self.v_decrease = velocity_decrease
        self.death = False

    def update(self):
        self.pos[0] += math.cos(self.angle) * (self.velocity / self.v_decrease)
        self.pos[1] += math.sin(self.angle) * (self.velocity / self.v_decrease)
        self.velocity -= 0.1

        if self.velocity <= 0:
            self.death = True

class Spark(Emitter):
    def __init__(self, game, pos, velocity, angle, v_decrease):
        super().__init__(game, pos, velocity, angle, v_decrease)

    def update(self):
        super().update()

    def render(self, surf, offset=(0, 0)):
            render_points = [
                (self.pos[0] + math.cos(self.angle) * self.velocity * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.velocity * 3 - offset[1]),
                (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.velocity * 0.5 - offset[0], self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.velocity * 0.5 - offset[1]),
                (self.pos[0] + math.cos(self.angle + math.pi) * self.velocity * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.velocity * 3 - offset[1]),
                (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.velocity * 0.5 - offset[0], self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.velocity * 0.5 - offset[1]),
            ]
            
            pygame.draw.polygon(surf, (255, 255, 255), render_points)

class Particle(Emitter):
    def __init__(self, game, pos, velocity, angle, v_decrease):
        super().__init__(game, pos, velocity, angle, v_decrease)

    def update(self):
        super().update()

    def render(self, surf, offset=(0,0)):
        pygame.draw.circle(surf, (255,255,255), (self.pos[0] - offset[0], self.pos[1] - offset[1]), self.velocity)