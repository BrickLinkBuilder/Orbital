import pygame, os, json, sys
from collections import deque

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

BASE_PATH = resource_path('data/images')
MAPS_PATH = resource_path('maps')

def load_image(path):
    img = pygame.image.load(os.path.join(BASE_PATH, path)).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path, frames):
    img_frames = []
    for i in range(frames):
        img = pygame.image.load(
            os.path.join(BASE_PATH, path, f'{i}.png')
        ).convert()
        img.set_colorkey((0, 0, 0))
        img_frames.append(img)
    return img_frames

def render_txt(text, pos, font, display):
    txt = font.render(str(text), False, (255,255,255))
    display.blit(txt, pos)
            
def fill(start, tilemap, layer, index, group, tile_size=16, bounds=None):
    existing = {(int(t['pos'][0]), int(t['pos'][1]))for t in tilemap.values() if t['layer'] == layer}
    if bounds is None:
        if not existing:
            return tilemap
        min_x = min(p[0] for p in existing)
        max_x = max(p[0] for p in existing)
        min_y = min(p[1] for p in existing)
        max_y = max(p[1] for p in existing)
    else:
        min_x, min_y, max_x, max_y = bounds

    sx = int(start[0]) * tile_size
    sy = int(start[1]) * tile_size

    queue = deque([(sx, sy)])
    visited = {(sx, sy)}

    while queue:
        x, y = queue.popleft()
        if x < min_x or x > max_x or y < min_y or y > max_y:
            continue
        if (x, y) in existing:
            continue

        tilemap[f"{x};{y};{layer}"] = {'type': group, 'index': index,'flipped_x': False, 'flipped_y': False,'pos': (x, y), 'layer': layer}
        existing.add((x, y))

        for dx, dy in ((tile_size, 0), (-tile_size, 0), (0, tile_size), (0, -tile_size)):
            n = (x + dx, y + dy)
            if n not in visited:
                visited.add(n)
                queue.append(n)

    return tilemap

def draw_grid(display, size, offset):
    for x in range(0, display.get_width(), size):
        ren_x = x - offset[0] % size
        pygame.draw.line(display, (15,15,15), (ren_x, 0), (ren_x, display.get_height()))
    for y in range(0, display.get_height(), size):
        ren_y = y - offset[1] % size
        pygame.draw.line(display, (15,15,15), (0, ren_y), (display.get_width(), ren_y))

def save_tilemap(path, tilemap):
    os.makedirs(MAPS_PATH, exist_ok=True)

    data = {}
    for tile in tilemap:
        data[str(tile)] = tilemap[tile]

    with open(os.path.join(MAPS_PATH, f'{path}.json'), 'w') as file:
        json.dump(data, file, indent=3)

def load_data(path):
    with open(os.path.join(MAPS_PATH, f'{path}.json'), 'r') as file:
        return json.load(file)

#only for level editor, used to load tilemap back into editor      
def load_tilemap(map, tilemap):
    data = load_data(map)

    return data

def get_bounds(tilemap):
    x = [tile['pos'][0] for tile in tilemap.values()]
    y = [tile['pos'][1] for tile in tilemap.values()]

    return (x, y)