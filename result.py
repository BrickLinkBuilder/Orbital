"""
TINY LIGHT  -  a little light drifting between giant planets
=============================================================
Theme: "I'm just a little guy"

Controls
  Mouse   : press near the light, drag BACK (like a slingshot), release to launch
  R       : restart level
  SPACE   : continue on title / level complete screens
  ESC     : quit

Requires:  pip install pygame      (no other packages needed)

Optional:  drop a  player.png  next to this file (e.g. 12x14 pixel art, feet
           pointing down) and set USE_SPRITE = True to replace the glowing orb.
"""
import math
import os
import random
import sys

import pygame

# --------------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------------
W, H = 960, 600
FPS = 60
PLAYER_R = 5              # collision radius of the light
MAX_PULL = 130            # max drag distance (pixels)
POWER = 0.07              # drag distance -> launch speed
FLIGHT_LIMIT = 170        # frames your light lasts in flight (also the preview length)
TRAIL_LEN = 28
GRACE_FRAMES = 12         # frames after launch where the origin planet is ignored
WORLD_MARGIN = 220        # how far outside the level you can fly before "lost"

USE_SPRITE = False
SPRITE_FILE = "player.png"
SPRITE_SCALE = 3

LIGHT_COL = (255, 233, 168)
BG_TOP = (10, 10, 36)
BG_BOTTOM = (34, 20, 64)

# --------------------------------------------------------------------------
# NOISE  (small self-contained 3D value noise, so no extra packages)
# --------------------------------------------------------------------------


def _rand(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1274126177 + seed * 362437) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def _smooth(t):
    return t * t * (3 - 2 * t)


def _lerp(a, b, t):
    return a + (b - a) * t


def value_noise(x, y, z, seed):
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = _smooth(x - ix), _smooth(y - iy), _smooth(z - iz)
    c000 = _rand(ix, iy, iz, seed)
    c100 = _rand(ix + 1, iy, iz, seed)
    c010 = _rand(ix, iy + 1, iz, seed)
    c110 = _rand(ix + 1, iy + 1, iz, seed)
    c001 = _rand(ix, iy, iz + 1, seed)
    c101 = _rand(ix + 1, iy, iz + 1, seed)
    c011 = _rand(ix, iy + 1, iz + 1, seed)
    c111 = _rand(ix + 1, iy + 1, iz + 1, seed)
    x00 = _lerp(c000, c100, fx)
    x10 = _lerp(c010, c110, fx)
    x01 = _lerp(c001, c101, fx)
    x11 = _lerp(c011, c111, fx)
    return _lerp(_lerp(x00, x10, fy), _lerp(x01, x11, fy), fz)


def fbm(x, y, z, seed, octaves=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for _ in range(octaves):
        total += value_noise(x, y, z, seed) * amp
        norm += amp
        x, y, z, amp = x * 2.0, y * 2.0, z * 2.0, amp * 0.5
    return total / norm


# --------------------------------------------------------------------------
# PLANET TEXTURES
# --------------------------------------------------------------------------
PALETTES = {
    "earth": [(0.38, (38, 84, 168)), (0.46, (226, 206, 150)), (0.62, (72, 150, 84)),
              (0.76, (120, 108, 98)), (9, (240, 240, 246))],
    "desert": [(0.35, (176, 98, 62)), (0.52, (212, 140, 86)), (0.70, (232, 184, 120)),
               (9, (246, 222, 170))],
    "ice": [(0.40, (110, 160, 224)), (0.60, (170, 208, 240)), (9, (236, 246, 255))],
    "rock": [(0.40, (92, 82, 92)), (0.62, (136, 124, 132)), (9, (176, 166, 172))],
    "gas": [(0.30, (83, 74, 183)), (0.55, (127, 119, 221)), (0.80, (175, 169, 236)),
            (9, (206, 203, 246))],
    "lava": [(0.40, (150, 40, 40)), (0.60, (226, 75, 74)), (0.80, (239, 159, 39)),
             (9, (250, 224, 150))],
    "goal": [(0.40, (15, 110, 86)), (0.62, (29, 158, 117)), (0.80, (93, 202, 165)),
             (9, (225, 245, 238))],
    "pink": [(0.40, (153, 53, 86)), (0.62, (212, 83, 126)), (0.82, (237, 147, 177)),
             (9, (250, 220, 232))],
}
GLOW_COLORS = {
    "earth": (70, 120, 220), "desert": (210, 130, 80), "ice": (130, 180, 240),
    "rock": (120, 110, 130), "gas": (127, 119, 221), "lava": (239, 100, 60),
    "goal": (93, 202, 165), "pink": (237, 147, 177),
}
_LIGHT = (-0.55, -0.6, 0.6)
_LN = math.sqrt(sum(c * c for c in _LIGHT))
LIGHT_DIR = tuple(c / _LN for c in _LIGHT)

_planet_cache = {}


def make_planet_surface(r, seed, style):
    """Generate a noise planet. Rendered at half size, then scaled up for a chunky
    pixel-art look (and so generation stays fast)."""
    key = (r, seed, style)
    if key in _planet_cache:
        return _planet_cache[key]
    palette = PALETTES[style]
    bands = style == "gas"
    res = max(8, r // 2)
    surf = pygame.Surface((res * 2, res * 2), pygame.SRCALPHA)
    for py in range(res * 2):
        for px in range(res * 2):
            x = (px - res + 0.5) / res
            y = (py - res + 0.5) / res
            d2 = x * x + y * y
            if d2 > 1:
                continue
            z = math.sqrt(1 - d2)
            if bands:
                warp = (fbm(x * 1.6, y * 1.6, z * 1.6, seed) - 0.5) * 6
                n = 0.5 + 0.5 * math.sin(y * 6.5 + warp)
            else:
                n = fbm(x * 2.2, y * 2.2, z * 2.2, seed)
                n = min(1.0, max(0.0, (n - 0.5) * 1.9 + 0.5))
            color = palette[-1][1]
            for threshold, col in palette:
                if n < threshold:
                    color = col
                    break
            shade = max(0.25, x * LIGHT_DIR[0] + y * LIGHT_DIR[1] + z * LIGHT_DIR[2])
            surf.set_at((px, py), (int(color[0] * shade), int(color[1] * shade),
                                   int(color[2] * shade), 255))
    big = pygame.transform.scale(surf, (r * 2, r * 2))
    _planet_cache[key] = big
    return big


_glow_cache = {}


def get_glow(radius, color, strength=1.0):
    radius = max(2, int(radius))
    key = (radius, color, round(strength, 2))
    if key not in _glow_cache:
        s = pygame.Surface((radius * 2, radius * 2))
        for rr in range(radius, 0, -1):
            k = (1 - rr / radius) ** 2 * strength
            pygame.draw.circle(s, (min(255, int(color[0] * k)), min(255, int(color[1] * k)),
                                   min(255, int(color[2] * k))), (radius, radius), rr)
        _glow_cache[key] = s
    return _glow_cache[key]


def draw_glow(surf, x, y, radius, color, strength=1.0):
    radius = max(2, int(radius))
    g = get_glow(radius, color, strength)
    surf.blit(g, (x - radius, y - radius), special_flags=pygame.BLEND_RGB_ADD)


# --------------------------------------------------------------------------
# BODIES  (planets, goal, hazards ...)
# --------------------------------------------------------------------------
LETHAL = ("sun", "blackhole", "asteroid")
LANDABLE = ("planet", "goal", "repulsor")


class Body:
    def __init__(self, kind, x, y, r, style="earth", seed=1):
        self.kind, self.x, self.y, self.r = kind, x, y, r
        self.style, self.seed = style, seed
        if kind == "planet" or kind == "goal":
            self.mass = r * r * 0.6
        elif kind == "sun":
            self.mass = r * r * 0.6
        elif kind == "blackhole":
            self.mass = 2200
        elif kind == "repulsor":
            self.mass = -r * r * 0.8
        else:  # asteroid
            self.mass = 0
        self.hit_r = r * 0.4 if kind == "blackhole" else r
        self._surf = None

    @property
    def surf(self):
        if self._surf is None:
            self._surf = make_planet_surface(self.r, self.seed, self.style)
        return self._surf

    def draw(self, screen, cx, cy, t):
        x, y, r = self.x - cx, self.y - cy, self.r
        pad = r * 2 + 60
        if x < -pad or x > W + pad or y < -pad or y > H + pad:
            return
        k = self.kind
        if k == "planet":
            draw_glow(screen, x, y, r + 26, GLOW_COLORS[self.style], 0.35)
            screen.blit(self.surf, (x - r, y - r))
        elif k == "goal":
            pulse = math.sin(t * 3)
            draw_glow(screen, x, y, r + 46 + 5 * pulse, GLOW_COLORS["goal"], 0.9)
            draw_glow(screen, x, y, r + 22, (200, 255, 230), 0.35)
            screen.blit(self.surf, (x - r, y - r))
        elif k == "sun":
            draw_glow(screen, x, y, r + 50, (255, 120, 60), 0.8)
            for i in range(12):
                a = t * 0.6 + i * math.pi / 6
                w = 0.13
                pts = [(x + math.cos(a - w) * (r - 3), y + math.sin(a - w) * (r - 3)),
                       (x + math.cos(a) * (r + 14), y + math.sin(a) * (r + 14)),
                       (x + math.cos(a + w) * (r - 3), y + math.sin(a + w) * (r - 3))]
                pygame.draw.polygon(screen, (239, 159, 39), pts)
            screen.blit(self.surf, (x - r, y - r))
        elif k == "blackhole":
            draw_glow(screen, x, y, r * 1.7, (110, 80, 255), 0.55)
            pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), int(r * 0.5))
            pygame.draw.circle(screen, (175, 169, 236), (int(x), int(y)), int(r * 0.5), 2)
            rect = pygame.Rect(x - r * 0.9, y - r * 0.9, r * 1.8, r * 1.8)
            for i in range(3):
                s = t * 2.2 + i * 2.1
                pygame.draw.arc(screen, (127, 119, 221), rect, s, s + 1.3, 4)
            rect2 = pygame.Rect(x - r * 0.68, y - r * 0.68, r * 1.36, r * 1.36)
            for i in range(2):
                s = -t * 3 + i * 3.1
                pygame.draw.arc(screen, (175, 169, 236), rect2, s, s + 1.0, 3)
        elif k == "repulsor":
            for i in range(3):
                ph = (t * 0.5 + i / 3) % 1
                f = 1 - ph
                col = (int(237 * f * 0.8), int(147 * f * 0.8), int(177 * f * 0.8))
                pygame.draw.circle(screen, col, (int(x), int(y)), int(r + 4 + ph * 34), 2)
            screen.blit(self.surf, (x - r, y - r))
        else:  # asteroid
            screen.blit(self.surf, (x - r, y - r))


# --------------------------------------------------------------------------
# LEVELS      (kind, x, y, radius, style, seed)     body[0] is where you start
# --------------------------------------------------------------------------
LEVELS = [
    dict(name="First hop", note="Drag back from the light and let go. Your light fades in flight.",
         size=(1250, 600), par=1, bodies=[
             ("planet", 170, 430, 42, "earth", 3),
             ("goal", 980, 280, 46, "goal", 5)]),
    dict(name="Around the big one", note="Big planets pull hard. Use that.",
         size=(1800, 700), par=2, bodies=[
             ("planet", 160, 520, 40, "desert", 7),
             ("planet", 800, 380, 78, "gas", 2),
             ("planet", 1180, 580, 32, "ice", 4),
             ("goal", 1600, 300, 46, "goal", 5)]),
    dict(name="Rock garden", note="Asteroids are not friendly.",
         size=(1900, 700), par=2, bodies=[
             ("planet", 150, 350, 40, "ice", 11),
             ("planet", 820, 190, 40, "rock", 6),
             ("asteroid", 520, 330, 16, "rock", 21),
             ("asteroid", 640, 470, 20, "rock", 22),
             ("asteroid", 1050, 330, 18, "rock", 23),
             ("asteroid", 1250, 520, 22, "rock", 24),
             ("asteroid", 1400, 250, 16, "rock", 25),
             ("goal", 1720, 420, 46, "goal", 5)]),
    dict(name="Too close to the sun", note="Red means no.",
         size=(1850, 700), par=3, bodies=[
             ("planet", 150, 380, 40, "desert", 9),
             ("planet", 560, 570, 36, "rock", 8),
             ("sun", 900, 340, 50, "lava", 4),
             ("planet", 1300, 140, 36, "ice", 12),
             ("goal", 1700, 400, 46, "goal", 5)]),
    dict(name="Event horizon", note="Some things you can't climb out of.",
         size=(1900, 700), par=3, bodies=[
             ("planet", 150, 520, 40, "earth", 14),
             ("planet", 600, 130, 34, "ice", 15),
             ("blackhole", 950, 330, 44, "rock", 1),
             ("planet", 1350, 560, 34, "desert", 16),
             ("goal", 1750, 200, 46, "goal", 5)]),
    dict(name="Push back", note="Not everything wants you close.",
         size=(1800, 700), par=3, bodies=[
             ("planet", 150, 330, 40, "gas", 17),
             ("planet", 520, 550, 36, "rock", 19),
             ("repulsor", 850, 330, 48, "pink", 18),
             ("planet", 1120, 570, 36, "ice", 20),
             ("asteroid", 560, 170, 18, "rock", 26),
             ("goal", 1650, 330, 46, "goal", 5)]),
    dict(name="Little guy, big universe", note="You made it this far. Go home.",
         size=(2400, 900), par=4, bodies=[
             ("planet", 150, 720, 40, "earth", 31),
             ("planet", 620, 520, 46, "gas", 32),
             ("sun", 1000, 250, 46, "lava", 33),
             ("repulsor", 1300, 700, 44, "pink", 34),
             ("blackhole", 1700, 450, 40, "rock", 1),
             ("planet", 1450, 150, 34, "ice", 35),
             ("asteroid", 850, 620, 18, "rock", 36),
             ("asteroid", 1150, 480, 16, "rock", 37),
             ("asteroid", 1950, 650, 20, "rock", 38),
             ("goal", 2250, 300, 50, "goal", 5)]),
]


def build_level(i):
    data = LEVELS[i]
    return [Body(*b) for b in data["bodies"]], data


# --------------------------------------------------------------------------
# PHYSICS  (pure functions - shared by the game, the preview and the tests)
# --------------------------------------------------------------------------


def accel(x, y, bodies):
    ax = ay = 0.0
    for b in bodies:
        if b.mass == 0:
            continue
        dx, dy = b.x - x, b.y - y
        d2 = max(dx * dx + dy * dy, 900.0)   # floor avoids crazy spikes up close
        d = math.sqrt(d2)
        f = b.mass / d2
        ax += f * dx / d
        ay += f * dy / d
    return ax, ay


def check_hit(x, y, bodies, ignore=None):
    for b in bodies:
        if b is ignore:
            continue
        rr = b.hit_r + PLAYER_R
        dx, dy = b.x - x, b.y - y
        if dx * dx + dy * dy < rr * rr:
            return b
    return None


def out_of_world(x, y, size):
    return (x < -WORLD_MARGIN or x > size[0] + WORLD_MARGIN or
            y < -WORLD_MARGIN or y > size[1] + WORLD_MARGIN)


def launch_velocity(px, py, mx, my):
    dx, dy = px - mx, py - my
    length = math.hypot(dx, dy)
    if length < 1:
        return 0.0, 0.0
    scale = min(length, MAX_PULL) / length * POWER
    return dx * scale, dy * scale


def simulate(x, y, vx, vy, bodies, ignore, steps, size):
    """Run the flight ahead of time. Returns (points, hit_body, status)."""
    pts = []
    for i in range(steps):
        ax, ay = accel(x, y, bodies)
        vx += ax
        vy += ay
        x += vx
        y += vy
        pts.append((x, y))
        hit = check_hit(x, y, bodies, ignore if i < GRACE_FRAMES else None)
        if hit:
            return pts, hit, "hit"
        if out_of_world(x, y, size):
            return pts, None, "lost"
    return pts, None, "timeout"


# --------------------------------------------------------------------------
# GAME
# --------------------------------------------------------------------------


def draw_star(surf, cx, cy, R, color):
    pts = []
    for i in range(10):
        a = i * math.pi / 5 - math.pi / 2
        d = R if i % 2 == 0 else R * 0.45
        pts.append((cx + math.cos(a) * d, cy + math.sin(a) * d))
    pygame.draw.polygon(surf, color, pts)


class Player:
    def __init__(self):
        self.x = self.y = self.vx = self.vy = 0.0
        self.flying = False
        self.on = None
        self.ignore = None
        self.ignore_t = 0
        self.flight_t = 0
        self.trail = []

    def place_on(self, body, angle=-math.pi / 2):
        self.x = body.x + math.cos(angle) * (body.r + PLAYER_R)
        self.y = body.y + math.sin(angle) * (body.r + PLAYER_R)
        self.vx = self.vy = 0.0
        self.flying = False
        self.on = body


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tiny Light")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.font_big = pygame.font.Font(None, 76)
        self.font_mid = pygame.font.Font(None, 40)
        self.bg = self.make_bg()
        rng = random.Random(4)
        self.stars = [[(rng.random() * W, rng.random() * H, rng.choice((1, 1, 2)),
                        rng.randint(90, 220), rng.random() * 6.28) for _ in range(70)]
                      for _ in range(3)]
        self.sprite = None
        if USE_SPRITE and os.path.exists(SPRITE_FILE):
            img = pygame.image.load(SPRITE_FILE).convert_alpha()
            self.sprite = pygame.transform.scale(
                img, (img.get_width() * SPRITE_SCALE, img.get_height() * SPRITE_SCALE))
        self.best = [0] * len(LEVELS)
        self.t = 0.0
        self.mode = "title"      # title | play | dying | complete | win
        self.level = 0
        self.particles = []
        self.shake = 0.0
        self.toast, self.toast_t = "", 0
        self.aiming = False
        self.load_level(0)

    # ------------------------------------------------------------------
    def make_bg(self):
        s = pygame.Surface((W, H))
        for y in range(H):
            k = y / H
            c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3))
            pygame.draw.line(s, c, (0, y), (W, y))
        return s

    def load_level(self, i):
        self.level = i
        self.bodies, self.data = build_level(i)
        self.size = self.data["size"]
        self.goal = next(b for b in self.bodies if b.kind == "goal")
        self.player = Player()
        self.player.place_on(self.bodies[0])
        self.launches = 0
        self.particles = []
        self.aiming = False
        self.dead_t = 0
        self.intro = 90
        self.cam = [0.0, 0.0]
        self.cam = list(self.cam_target(self.goal.x, self.goal.y))
        self.toast, self.toast_t = self.data["note"], 240

    def cam_target(self, fx, fy):
        tx = fx - W / 2
        ty = fy - H / 2
        tx = max(0, min(tx, self.size[0] - W)) if self.size[0] > W else (self.size[0] - W) / 2
        ty = max(0, min(ty, self.size[1] - H)) if self.size[1] > H else (self.size[1] - H) / 2
        return tx, ty

    # ------------------------------------------------------------------
    def burst(self, x, y, color, n=20, speed=3.0):
        for _ in range(n):
            a = random.random() * math.tau
            s = random.random() * speed
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s,
                                   random.randint(20, 45), color])

    def die(self, msg):
        p = self.player
        self.burst(p.x, p.y, LIGHT_COL, 28, 4)
        self.shake = 9
        p.flying = False
        p.vx = p.vy = 0
        self.mode = "dying"
        self.dead_t = 45
        self.toast, self.toast_t = msg, 70

    def land(self, body):
        p = self.player
        angle = math.atan2(p.y - body.y, p.x - body.x)
        p.place_on(body, angle)
        self.shake = max(self.shake, 4)
        self.burst(p.x, p.y, LIGHT_COL, 10, 2)
        if body.kind == "goal":
            self.burst(p.x, p.y, (93, 202, 165), 50, 5)
            n, par = self.launches, self.data["par"]
            stars = 3 if n <= par else 2 if n <= par + 1 else 1
            self.best[self.level] = max(self.best[self.level], stars)
            self.mode = "complete"

    def try_launch(self, mx, my):
        p = self.player
        vx, vy = launch_velocity(p.x, p.y, mx, my)
        if math.hypot(vx, vy) < 0.5:
            return
        p.vx, p.vy = vx, vy
        p.flying = True
        p.ignore, p.ignore_t = p.on, GRACE_FRAMES
        p.flight_t = 0
        self.launches += 1
        self.burst(p.x, p.y, LIGHT_COL, 8, 1.5)

    # ------------------------------------------------------------------
    def world_mouse(self):
        mx, my = pygame.mouse.get_pos()
        return mx + self.cam[0], my + self.cam[1]

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key == pygame.K_r and self.mode in ("play", "dying"):
                    self.load_level(self.level)
                    self.mode = "play"
                if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.advance_screen()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.mode in ("title", "complete", "win"):
                    self.advance_screen()
                elif self.mode == "play" and not self.player.flying:
                    wx, wy = self.world_mouse()
                    if math.hypot(wx - self.player.x, wy - self.player.y) < 70:
                        self.aiming = True
            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if self.aiming:
                    self.aiming = False
                    wx, wy = self.world_mouse()
                    self.try_launch(wx, wy)
        return True

    def advance_screen(self):
        if self.mode == "title":
            self.load_level(0)
            self.mode = "play"
        elif self.mode == "complete":
            if self.level + 1 < len(LEVELS):
                self.load_level(self.level + 1)
                self.mode = "play"
            else:
                self.mode = "win"
        elif self.mode == "win":
            self.load_level(0)
            self.mode = "title"

    # ------------------------------------------------------------------
    def update(self):
        self.t += 1 / FPS
        p = self.player
        if self.mode == "play" and p.flying:
            ax, ay = accel(p.x, p.y, self.bodies)
            p.vx += ax
            p.vy += ay
            p.x += p.vx
            p.y += p.vy
            p.trail.append((p.x, p.y))
            p.flight_t += 1
            hit = check_hit(p.x, p.y, self.bodies, p.ignore if p.ignore_t > 0 else None)
            if p.ignore_t > 0:
                p.ignore_t -= 1
            if hit:
                if hit.kind in LETHAL:
                    self.die({"sun": "Too hot.", "blackhole": "Swallowed.",
                              "asteroid": "Ouch."}[hit.kind])
                else:
                    self.land(hit)
            elif out_of_world(p.x, p.y, self.size):
                self.die("Lost in space.")
            elif p.flight_t >= FLIGHT_LIMIT:
                self.die("Out of light.")
        if len(p.trail) > TRAIL_LEN or (not p.flying and p.trail):
            p.trail.pop(0)

        if self.mode == "dying":
            self.dead_t -= 1
            if self.dead_t <= 0:
                self.load_level(self.level)
                self.mode = "play"

        # camera
        if self.intro > 0 and self.mode == "play":
            self.intro -= 1
            tx, ty = self.cam_target(self.goal.x, self.goal.y) if self.intro > 30 \
                else self.cam_target(p.x, p.y)
        else:
            tx, ty = self.cam_target(p.x, p.y)
        ease = 0.06 if self.mode != "complete" else 0.04
        self.cam[0] += (tx - self.cam[0]) * ease
        self.cam[1] += (ty - self.cam[1]) * ease

        self.shake *= 0.85
        if self.toast_t > 0:
            self.toast_t -= 1
        for q in self.particles:
            q[0] += q[2]
            q[1] += q[3]
            q[2] *= 0.96
            q[3] *= 0.96
            q[4] -= 1
        self.particles = [q for q in self.particles if q[4] > 0]

    # ------------------------------------------------------------------
    def draw_text(self, text, font, color, center=None, topleft=None, topright=None):
        img = font.render(text, True, color)
        r = img.get_rect()
        if center:
            r.center = center
        if topleft:
            r.topleft = topleft
        if topright:
            r.topright = topright
        self.screen.blit(img, r)

    def draw(self):
        scr = self.screen
        scr.blit(self.bg, (0, 0))
        sx = random.uniform(-self.shake, self.shake) if self.shake > 0.3 else 0
        sy = random.uniform(-self.shake, self.shake) if self.shake > 0.3 else 0
        cx, cy = self.cam[0] - sx, self.cam[1] - sy

        # parallax stars
        for layer, f in zip(self.stars, (0.08, 0.2, 0.4)):
            for (x, y, s, b, ph) in layer:
                px = (x - cx * f) % W
                py = (y - cy * f) % H
                br = int(b * (0.65 + 0.35 * math.sin(self.t * 2 + ph)))
                scr.fill((br, br, br), (px, py, s, s))

        for b in self.bodies:
            b.draw(scr, cx, cy, self.t)

        if self.mode != "title":
            self.draw_player(cx, cy)
            if self.aiming and not self.player.flying:
                self.draw_aim(cx, cy)

        for (x, y, vx, vy, life, col) in self.particles:
            f = min(1.0, life / 25)
            pygame.draw.circle(scr, (int(col[0] * f), int(col[1] * f), int(col[2] * f)),
                               (int(x - cx), int(y - cy)), 2)

        self.draw_ui()

    def draw_player(self, cx, cy):
        p, scr = self.player, self.screen
        if self.mode == "dying":
            return
        for i, (tx, ty) in enumerate(p.trail):
            f = (i + 1) / len(p.trail)
            draw_glow(scr, tx - cx, ty - cy, 2 + 9 * f, LIGHT_COL, 0.55 * f)
        x, y = p.x - cx, p.y - cy
        left = 1.0 - (p.flight_t / FLIGHT_LIMIT if p.flying else 0.0)
        size = 10 + 16 * left
        flicker = 0.5 + 0.5 * math.sin(self.t * 40) if left < 0.25 else 1.0
        draw_glow(scr, x, y, size + 3 * math.sin(self.t * 4), LIGHT_COL, 0.9 * flicker)
        if self.sprite:
            img = self.sprite
            if p.on and not p.flying:
                ang = math.degrees(math.atan2(-(p.y - p.on.y), p.x - p.on.x)) - 90
                img = pygame.transform.rotate(self.sprite, ang)
            scr.blit(img, img.get_rect(center=(x, y)))
        else:
            pygame.draw.circle(scr, (255, 255, 255), (int(x), int(y)), PLAYER_R)

    def draw_aim(self, cx, cy):
        p, scr = self.player, self.screen
        wx, wy = self.world_mouse()
        vx, vy = launch_velocity(p.x, p.y, wx, wy)
        if math.hypot(vx, vy) < 0.5:
            return
        pts, hit, status = simulate(p.x, p.y, vx, vy, self.bodies, p.on,
                                    FLIGHT_LIMIT, self.size)
        n = len(pts)
        for i in range(4, n, 5):
            f = 1 - i / max(n, 1)
            pygame.draw.circle(scr, (int(255 * (0.3 + 0.7 * f)),) * 3,
                               (int(pts[i][0] - cx), int(pts[i][1] - cy)),
                               max(1, int(3 * f + 0.5)))
        if status == "timeout" and pts:
            ex, ey = int(pts[-1][0] - cx), int(pts[-1][1] - cy)
            pygame.draw.line(scr, (255, 120, 120), (ex - 5, ey - 5), (ex + 5, ey + 5), 2)
            pygame.draw.line(scr, (255, 120, 120), (ex - 5, ey + 5), (ex + 5, ey - 5), 2)
        # pull indicator
        d = min(math.hypot(wx - p.x, wy - p.y), MAX_PULL)
        a = math.atan2(wy - p.y, wx - p.x)
        end = (p.x + math.cos(a) * d - cx, p.y + math.sin(a) * d - cy)
        pygame.draw.line(scr, (120, 120, 160), (p.x - cx, p.y - cy), end, 1)
        pygame.draw.circle(scr, (120, 120, 160), (int(end[0]), int(end[1])), 4, 1)

    def draw_ui(self):
        scr = self.screen
        if self.mode == "title":
            self.dim(120)
            self.draw_text("TINY LIGHT", self.font_big, (255, 240, 200), center=(W // 2, 210))
            self.draw_text("a little light in a very big universe", self.font_mid,
                           (180, 180, 220), center=(W // 2, 275))
            blink = 0.6 + 0.4 * math.sin(self.t * 3)
            c = int(255 * blink)
            self.draw_text("click to start", self.font, (c, c, c), center=(W // 2, 380))
            return
        if self.mode == "win":
            self.dim(170)
            self.draw_text("You made it home.", self.font_big, (255, 240, 200),
                           center=(W // 2, 220))
            total = sum(self.best)
            self.draw_text("Stars collected: %d / %d" % (total, len(LEVELS) * 3),
                           self.font_mid, (200, 200, 235), center=(W // 2, 300))
            self.draw_text("click to play again", self.font, (160, 160, 200),
                           center=(W // 2, 370))
            return

        self.draw_text("%d. %s" % (self.level + 1, self.data["name"]), self.font,
                       (210, 210, 240), topleft=(18, 14))
        self.draw_text("launches %d   par %d" % (self.launches, self.data["par"]), self.font,
                       (210, 210, 240), topright=(W - 18, 14))
        self.draw_text("drag back from the light to aim   |   R = restart", self.font,
                       (110, 110, 150), center=(W // 2, H - 18))
        if self.toast_t > 0:
            f = min(1.0, self.toast_t / 40)
            c = int(255 * f)
            self.draw_text(self.toast, self.font_mid, (c, c, c), center=(W // 2, 70))

        if self.mode == "complete":
            self.dim(110)
            self.draw_text("Level complete", self.font_big, (255, 240, 200),
                           center=(W // 2, 200))
            n, par = self.launches, self.data["par"]
            stars = 3 if n <= par else 2 if n <= par + 1 else 1
            for i in range(3):
                col = (255, 214, 77) if i < stars else (70, 70, 100)
                draw_star(scr, W // 2 - 70 + i * 70, 290, 28, col)
            self.draw_text("%d launches (par %d)" % (n, par), self.font_mid,
                           (200, 200, 235), center=(W // 2, 360))
            self.draw_text("click or SPACE to continue", self.font, (160, 160, 200),
                           center=(W // 2, 410))

    def dim(self, alpha):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((5, 5, 20, alpha))
        self.screen.blit(s, (0, 0))

    # ------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()