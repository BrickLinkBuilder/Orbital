
import math
import random
import pygame
from noise import pnoise2


PALETTES = [
    [(15, 35, 100), (35, 100, 190), (130, 190, 245)],
    [(65, 25, 120), (130, 65, 190), (210, 165, 245)],
    [(100, 45, 25), (185, 95, 45), (245, 190, 105)],
    [(90, 15, 30), (175, 35, 55), (245, 115, 125)],
    [(45, 80, 120), (125, 185, 220), (225, 245, 255)],
    [(110, 30, 85), (200, 75, 145), (255, 180, 215)],
    [(100, 65, 15), (190, 140, 35), (255, 225, 125)],
    [(55, 55, 70), (125, 130, 145), (220, 220, 230)],
    [(10, 20, 65), (30, 55, 140), (90, 130, 235)],
    [(75, 15, 100), (165, 35, 175), (240, 125, 230)],
]
GOAL_PALETTE = [(12, 65, 30), (30, 155, 65),(125, 235, 85)]

class Planet:
    def __init__(self, game, pos, type, gravity_strength, radius, player):
        self.game = game
        self.pos = list(pos)
        self.type = type
        self.g_strength = gravity_strength
        self.radius = radius
        self.player = player
        if self.type == 'goal':
            self.palette = GOAL_PALETTE
        else:
            self.palette = random.choice(PALETTES)
        self.terrain_scale = random.choice([0.03, 0.05, 0.08])
        self.texture = self.gen_texture()

    def gen_texture(self):
        size = self.radius * 2
        texture = pygame.Surface((size, size), pygame.SRCALPHA)

        for x in range(size):
            for y in range(size):
                dx = x - self.radius
                dy = y - self.radius
                distance = math.hypot(dx, dy)

                if distance <= self.radius:
                    value = pnoise2(x * self.terrain_scale,y * self.terrain_scale)

                    if value < -0.1:
                        color = self.palette[0]
                    elif value < 0.1:
                        color = self.palette[1]
                    else:
                        color = self.palette[2]

                    nx = dx / self.radius
                    ny = dy / self.radius

                    light = max(0.2, 1 - (nx + ny) * 0.25)

                    steps = 4
                    light = round(light * steps) / steps
                    color = tuple(max(0, min(255, int(channel * light))) for channel in color)
                    texture.set_at((x, y), color)

        return texture

    def render(self, surf, offset):
        x = int(self.pos[0] - offset[0])
        y = int(self.pos[1] - offset[1])

        ring_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for i in range(1, 3):
            ring_radius = self.radius + i * 25
            pygame.draw.circle(ring_surf,(*self.palette[1], 100),(x, y),ring_radius, i)

        surf.blit(ring_surf, (0, 0))

        glow_radius = self.radius + 4
        pulse = math.sin(pygame.time.get_ticks() * 0.003) * 2
        glow_size = glow_radius + pulse
        glow = pygame.Surface((int(glow_size * 2), int(glow_size * 2)),pygame.SRCALPHA)
        pygame.draw.circle(glow,(*self.palette[1], 60),(int(glow_size), int(glow_size)),int(glow_size))
        surf.blit(glow, (x - glow_radius, y - glow_radius))
        surf.blit(self.texture,(x - self.radius, y - self.radius))
        