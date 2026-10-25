
import math
import random
import pygame

class Asteroid:
    def __init__(self, game, pos, radius):
        self.game = game
        self.pos = list(pos)
        self.radius = radius
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 2.5)
        self.velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
        self.points = []
        point_count = 9
        for i in range(point_count):
            angle = math.tau * i / point_count
            distance = radius * random.uniform(0.75, 1.15)

            self.points.append((math.cos(angle) * distance,math.sin(angle) * distance))

    def update(self, frame_scale):
        self.pos[0] += self.velocity[0] * frame_scale
        self.pos[1] += self.velocity[1] * frame_scale

    def render(self, surf, offset):
        x = self.pos[0] - offset[0]
        y = self.pos[1] - offset[1]
        points = [(int(x + px), int(y + py)) for px, py in self.points]
        pygame.draw.polygon(surf, (95, 90, 105), points)
        pygame.draw.polygon(surf, (155, 145, 155), points, 1)

class BlackHole:
    def __init__(self, game, pos, radius=25, gravity=2.0):
        self.game = game
        self.pos = pygame.Vector2(pos)
        self.radius = radius
        self.gravity = gravity
        self.launch_speed = 12
        self.launch_angle = random.uniform(0, math.tau)

    def render(self, surf, offset=(0, 0)):
        pos = self.pos - pygame.Vector2(offset)
        x, y = int(pos.x), int(pos.y)
        glow = pygame.Surface((self.radius * 5, self.radius * 5), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 40, 180, 35), (self.radius * 2, self.radius * 2), self.radius * 2)
        surf.blit(glow, (x - self.radius * 2, y - self.radius * 2))
        pygame.draw.circle(surf, (150, 70, 255), (x, y), self.radius + 5, 3)
        pygame.draw.circle(surf, (5, 3, 12), (x, y),self.radius)
