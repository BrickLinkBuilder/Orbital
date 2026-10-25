import random
import sys
import math

import pygame

from planets import Planet
from tilemap import Tilemap
from player import Player
from assets import *
from effects import *
from objects import *
from config import *

class Game:
    def __init__(self):
        pygame.init()

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((900, 600))
        pygame.display.set_caption("Orbital")
        self.display = pygame.Surface((450, 300))
        self.ui_surf = pygame.Surface((450, 300), pygame.SRCALPHA)
        self.font = pygame.font.Font('font.ttf', 32)

        self.fade_alpha = 0
        self.fading = False
        self.fade_in = False
        self.fade_action = None

        self.gravity = 0.1
        self.power_scale = 0.1
        self.max_power = 15

        self.aiming = False
        self.is_moving = False

        self.offset = [0, 0]
        self.current_level = 0

        self.assets = images()
        self.sounds = sounds()
        self.sounds['explosion'].set_volume(0.3)
        self.tilemap = Tilemap(self)
        self.tilemap.get_tiles(self.current_level)
        self.b = self.tilemap.boundries
        pygame.mixer.music.load('data/sounds/music.wav')
        pygame.mixer.music.play(-1)

        self.planet_pos = self.tilemap.planets
        self.goal_pos = self.tilemap.goal
        self.blackhole_pos = self.tilemap.blackholes
        self.planets = []
        self.stars = []
        self.particles = []
        self.asteroids = []
        self.blackholes = []
        self.blackholes_triggered = set()
        self.pos = self.tilemap.player_spawn
        self.pause_time = 100
        self.player = Player(self, self.tilemap.player_spawn, 5, self.planets)
        self.spawn_stars()            
        self.shake_duration = 0
        for pos in self.planet_pos:
            self.planets.append(Planet(self, pos, 'planet', random.randint(200, 800), random.randint(35, 65), self.player))
        for pos in self.blackhole_pos:
            self.blackholes.append(BlackHole(self, pos, 40))
        self.planets.append(Planet(self, self.goal_pos, 'goal', 400, 15, self.player))
        if self.goal_pos != None:
            self.offset = [self.goal_pos[0] - self.display.get_width() / 2, self.goal_pos[1] - self.display.get_height() / 2]
        else:
            self.offset =[0, 0]

        self.asteroid_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.asteroid_timer, 500)

    def load_level(self, level):
        self.tilemap.get_tiles(level)
        self.b = self.tilemap.boundries
        self.player.death = False
        self.blackholes_triggered = set()
        self.planet_pos = self.tilemap.planets
        self.goal_pos = self.tilemap.goal
        self.blackhole_pos = self.tilemap.blackholes
        self.planets = []
        self.stars = []
        self.particles = []
        self.asteroids = []
        self.blackholes = []
        self.pos = self.tilemap.player_spawn
        self.aiming = False
        self.is_moving = False
        if self.goal_pos != None:
            self.offset = [self.goal_pos[0] - self.display.get_width() / 2, self.goal_pos[1] - self.display.get_height() / 2]
        else:
            self.offset =[0, 0]
        self.pause_time = 100
        self.player = Player(self, self.tilemap.player_spawn, 5, self.planets)
        self.spawn_stars()            
        self.shake_duration = 0
        for pos in self.planet_pos:
            self.planets.append(Planet(self, pos, 'planet', random.randint(200, 800), random.randint(35, 65), self.player))
        for pos in self.blackhole_pos:
            self.blackholes.append(BlackHole(self, pos, 40))
        self.planets.append(Planet(self, self.goal_pos, 'goal', 400, 15, self.player))

    def spawn_stars(self):
        for _ in range(random.randint(400, 700)):
            x = random.randint(self.b['left'] - 1000, self.b['right'] + 1000)
            y = random.randint(self.b['top'] - 1000, self.b['bottom'] + 1000)
            self.stars.append((random.choice(self.assets['stars']), x, y))

    def spawn_asteroids(self):
        x = random.randint(self.b['left'] - 500 , self.b['right'] + 500)
        y = random.randint(self.b['bottom'] - 500, self.b['bottom'] - 100)
        self.asteroids.append(Asteroid(self, (x, y), random.randint(8, 15)))

    def apply_blackhole_gravity(self):
        for b in self.blackholes:
            distance = math.hypot(b.pos[0] - self.player.pos[0], b.pos[1] - self.player.pos[1])

            if distance < self.player.size + b.radius:
                if b not in self.blackholes_triggered:
                    self.sounds['blackhole'].play()
                    self.blackholes_triggered.add(b)
                angle = b.launch_angle
                self.player.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * b.launch_speed
                b.launch_angle = random.uniform(0, math.tau)
            else:
                self.blackholes_triggered.discard(b)

    def get_aim(self):
        mx, my = pygame.mouse.get_pos()
        mx = mx / 2 + self.offset[0]
        my = my / 2 + self.offset[1]
        dx = self.player.pos[0] - mx
        dy = self.player.pos[1] - my

        angle = math.atan2(dy, dx)
        distance = math.sqrt((self.player.pos[0] - mx)**2 + (self.player.pos[1] - my)**2)
        power = min(distance * self.power_scale, self.max_power)

        return angle, power

    def check_asteroid_collision(self):
        for a in self.asteroids.copy():
            distance = math.sqrt((a.pos[0] - self.player.pos[0])**2 + (a.pos[1] - self.player.pos[1])**2)

            if distance < self.player.size + a.radius and not self.player.death:
                self.sounds['explosion'].play()
                self.player.death = True
                self.shake_duration = 10
                for i in range(20):
                    self.particles.append(Spark(self, self.player.pos, random.randint(4, 7), random.uniform(0, math.tau), 2))
                self.asteroids.remove(a)
                return

    def check_planet_collision(self):
        for p in self.planets:
            dx = self.player.pos[0] - p.pos[0]
            dy = self.player.pos[1] - p.pos[1]

            distance = math.hypot(dx, dy)
            min_distance = p.radius + self.player.size

            if distance < min_distance:
                if distance == 0:
                    continue
                nx = dx / distance
                ny = dy / distance

                self.player.pos[0] = p.pos[0] + nx * min_distance
                self.player.pos[1] = p.pos[1] + ny * min_distance

                self.player.velocity[0] = 0
                self.player.velocity[1] = 0
                self.is_moving = False
                for i in range(15):
                    self.particles.append(Spark(self, self.player.pos, random.randint(2, 4), random.uniform(0, math.tau), 1))
                    self.shake_duration = 10
                self.sounds['hit'].play()

                if p.type == 'goal' and not self.fading and not self.fade_in:
                    self.fading = True
                    self.current_level += 1
                    self.fade_action = lambda: self.load_level(self.current_level)

    def calculate_gravity(self, x, y):
        total_ax = 0
        total_ay = 0

        for p in self.planets:
            dx = p.pos[0] - x
            dy = p.pos[1] - y

            distance = math.hypot(dx, dy)
            distance = max(distance, p.radius + self.player.size)

            strength = p.g_strength / distance**2
            total_ax += (dx / distance) * strength
            total_ay += (dy / distance) * strength

        return total_ax, total_ay

    def draw_trajectory(self):
        angle, power = self.get_aim()
        vel_x = math.cos(angle) * power
        vel_y = math.sin(angle) * power
        pre_x, pre_y = self.player.pos
        points = [(round(pre_x), round(pre_y))]
        
        for i in range(170):
            ax, ay = self.calculate_gravity(pre_x, pre_y)
            vel_x += ax
            vel_y += ay
            pre_x += vel_x
            pre_y += vel_y

            points.append((round(pre_x), round(pre_y)))

            hit_planet = False

            for p in self.planets:
                dx = p.pos[0] - pre_x
                dy = p.pos[1] - pre_y
                distance = math.hypot(dx, dy)

                if distance <= p.radius + self.player.size:
                    hit_planet = True
                    break

            if hit_planet:
                break

        screen_points = [
            (round(x - self.offset[0]), round(y - self.offset[1])) for x, y in points]

        total_points = len(screen_points)

        for i in range(0, total_points, 6):
            x, y = screen_points[i]

            alpha = int(255 * (1 - i / total_points))

            dot = pygame.Surface((4, 4), pygame.SRCALPHA)
            dot.fill((180, 220, 255, alpha))

            self.display.blit(dot, (x - 2, y - 2))

    def update(self):
        while True:
            self.display.fill((0, 0, 22))
            self.ui_surf.fill((0, 0, 0, 0))

            for img, x, y in self.stars:
                self.display.blit(img, (x - self.offset[0], y - self.offset[1]))

            mx, my = pygame.mouse.get_pos()
            mx = mx / 2 + self.offset[0]
            my = my / 2 + self.offset[1]

            dt = self.clock.tick(60) / 1000
            frame_scale = dt * 60

            self.pause_time -= 1

            if self.pause_time > 0:
                self.offset[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.offset[0]) / 100
                self.offset[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.offset[1]) / 100
            else:
                self.offset[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.offset[0]) / 30
                self.offset[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.offset[1]) / 30

            if self.shake_duration > 0:
                self.shake_duration -= 1
                self.offset[0] += random.randint(1, 2)
                self.offset[1] += random.randint(1, 2)

            if self.pause_time < 0 and self.player.can_move:
                if self.aiming and not self.is_moving:
                    pygame.draw.line(self.display, (50, 50, 50), (self.player.pos[0] - self.offset[0], self.player.pos[1] - self.offset[1]), (mx - self.offset[0], my - self.offset[1]), 1)
                    pygame.draw.circle(self.display, (50, 50, 50), (mx - self.offset[0], my - self.offset[1]), 5, 1)
                    self.draw_trajectory()

            if self.is_moving:
                ax, ay = self.calculate_gravity(self.player.pos[0],self.player.pos[1])
                self.apply_blackhole_gravity()

                self.player.velocity[0] += ax * frame_scale
                self.player.velocity[1] += ay * frame_scale

                self.player.pos[0] += self.player.velocity[0] * frame_scale
                self.player.pos[1] += self.player.velocity[1] * frame_scale

                self.check_planet_collision()
            self.check_asteroid_collision()

            if not self.player.death:
                self.player.render(self.display, self.offset)
                speed = math.hypot(self.player.velocity[0], self.player.velocity[1])
                angle = math.atan2(self.player.velocity[1], self.player.velocity[0])

                if speed > 0.5:
                    if random.random() < 0.5:
                        self.particles.append(Particle(self, self.player.pos.copy(),random.randint(2, 3), angle + math.pi + random.uniform(-0.4, 0.4), 4))

            if self.player.pos[0] > self.tilemap.boundries['right'] + 500 or self.player.pos[0] < self.tilemap.boundries['left'] - 500:
                self.player.death = True
            if self.player.pos[1] > self.tilemap.boundries['bottom'] + 500 or self.player.pos[1] < self.tilemap.boundries['top'] - 500:
                self.player.death = True

            for p in self.planets:
                if self.current_level != 10:
                    p.render(self.display, self.offset)

            for b in self.blackholes:
                b.render(self.display, self.offset)

            for a in self.asteroids.copy():
                a.render(self.display, self.offset)
                a.update(frame_scale)
                for planet in self.planets:
                    dx = a.pos[0] - planet.pos[0]
                    dy = a.pos[1] - planet.pos[1]

                    distance = math.hypot(dx, dy)

                    if distance < a.radius + planet.radius:
                        for i in range(25):
                            self.particles.append(Spark(self, a.pos, random.randint(3, 6), random.uniform(0, math.tau), 2))
                        self.shake_duration = 4
                        self.sounds['explosion'].play()
                        self.asteroids.remove(a)
                        break

            for p in self.particles.copy():
                if not p.death:
                    p.update()
                    p.render(self.display, self.offset)
                else:
                    self.particles.remove(p)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == self.asteroid_timer and self.pause_time < 0 and self.player.can_move:
                    if 2 <= self.current_level < 4:
                        self.spawn_asteroids()
                    elif self.current_level >= 4:
                        for i in range(3):
                            self.spawn_asteroids()

                


                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not self.is_moving and self.player.can_move:
                            self.aiming = True

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and not self.is_moving and self.pause_time < 0 and self.player.can_move:
                        self.sounds['jump'].play()
                        self.aiming = False
                        self.is_moving = True
                        angle, power = self.get_aim()

                        self.player.velocity[0] = math.cos(angle) * power
                        self.player.velocity[1] = math.sin(angle) * power

                        self.shake_duration = 4
                        for i in range(10):
                            self.particles.append(Spark(self, self.player.pos, random.randint(2, 4), random.uniform(angle - 10, angle + 10), 1))

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.player.death and not self.fading:
                        self.fading = True
                        self.fade_action = lambda: self.load_level(self.current_level)

            if self.current_level != 10:
                render_txt('level: ' + str(self.current_level + 1), (10, 5), self.font, self.ui_surf)

            if self.current_level == 0 and not self.fading:
                render_txt("Reach the glowing orb to complete the level", (self.display.get_width() / 2 - 170, self.display.get_height() / 6), self.font, self.ui_surf)
                render_txt("Hold the left mouse button to aim Release to launch", (self.display.get_width() / 2 - 205, self.display.get_height() / 6 + 20), self.font, self.ui_surf)
            if self.current_level == 1 and not self.fading:
                render_txt("You can stick to planets to help you move", (self.display.get_width() / 2 - 170, self.display.get_height() / 6), self.font, self.ui_surf)
                render_txt("Planets gravity affects your trajectory", (self.display.get_width() / 2 - 170, self.display.get_height() / 6 + 20), self.font, self.ui_surf)
            if self.current_level == 2 and not self.fading:
                render_txt("You dont want to hit an asteroid", (self.display.get_width() / 2 - 150, self.display.get_height() / 6), self.font, self.ui_surf)
            if self.current_level == 4 and not self.fading:
                render_txt("Black holes can launch you anywhere", (self.display.get_width() / 2 - 150, self.display.get_height() / 6), self.font, self.ui_surf)
            if self.current_level == 10:
                self.player.can_move = False
                render_txt("Thank You for playing :) ", (self.display.get_height() / 2, self.display.get_height() / 2), self.font, self.ui_surf)
            if self.player.death and not self.fading:
                self.player.pos = [self.display.get_height() / 2, self.display.get_height() / 2]
                render_txt("Press R To Restart", (self.display.get_height() / 2, self.display.get_height() / 2), self.font, self.ui_surf)
            if self.fading:
                self.fade_alpha = min(255, self.fade_alpha + 8)

                if self.fade_alpha == 255:
                    self.fading = False

                    if self.fade_action:
                        action = self.fade_action
                        self.fade_action = None
                        action()

                    self.fade_in = True

            elif self.fade_in:
                self.fade_alpha = max(0, self.fade_alpha - 8)

                if self.fade_alpha == 0:
                    self.fade_in = False

            overlay = pygame.Surface(self.display.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.fade_alpha)
            self.display.blit(overlay, (0, 0))

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            self.screen.blit(pygame.transform.scale(self.ui_surf, self.screen.get_size()), (0, 0))
            pygame.display.flip()

if __name__ == "__main__":
    Game().update()
