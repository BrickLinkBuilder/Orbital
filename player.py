import pygame

class Player:
    def __init__(self, game, pos, size, planets):
        self.game = game
        self.pos = list(pos)
        self.size = size
        self.planets = planets
        self.velocity = [0, 0]
        self.death = False
        self.can_move = True

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size, self.size)

    def render(self, surf, offset):
        x = int(self.pos[0] - offset[0])
        y = int(self.pos[1] - offset[1])
        r = int(self.size)

        glow = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow,(35, 190, 255, 70), (r * 3, r * 3), r * 2)
        surf.blit(glow, (x - r * 3, y - r * 3))

        pygame.draw.circle(surf, (35, 190, 255), (x, y), r)
        pygame.draw.circle(surf, (220, 250, 255), (x, y), int(r * 0.65))
