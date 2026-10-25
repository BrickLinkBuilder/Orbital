import json
import pygame

from config import *

PLANETS = ('planet')
NEIGHBOR_OFFSETS = [(-1, -1), (0, -1), (1, -1), (-1,  0), (0,  0), (1,  0), (-1,  1), (0,  1), (1,  1)]

class Tilemap:
    def __init__(self, game):
        self.game = game
        self.tilemap = {}
        self.planets = {}
        self.player_spawn = ()
        self.goal = ()
        self.blackholes = {}
        self.boundries = {'top' : [], 'bottom' : [], 'right' : [], 'left' : []}

    def get_tiles(self, level):
        data = load_data(level)
        self.tilemap = data
        self.planets = {}
        self.blackholes = {}
        self.player_spawn = ()
        self.goal = ()

        for tile in self.tilemap:
            tile_data = self.tilemap[tile]
            tile_type = tile_data['type']
            pos = tile_data['pos']
            if tile_type in PLANETS:
                self.planets[(pos[0], pos[1])] = {}
            if tile_type == 'player_spawn':
                self.player_spawn = pos
            if tile_type == 'goal':
                self.goal = pos
            if tile_type == 'obstacle':
                self.blackholes[(pos[0], pos[1])] = {}

        self.set_bounds()

    def set_bounds(self):
        bounds = get_bounds(self.tilemap)

        self.boundries['left'] = min(bounds[0])
        self.boundries['right'] = max(bounds[0])
        self.boundries['top'] = min(bounds[1])
        self.boundries['bottom'] = max(bounds[1])

    def tiles_around(self, pos):
        tiles = []
    
        for offset in NEIGHBOR_OFFSETS:
            e_loc = ((int(pos[0] // 16) * 16 + offset[0] * 16), int(pos[1] // 16) * 16 + offset[1] * 16)
            if e_loc in self.physics_tiles:
                tiles.append(e_loc)
        return tiles
        
    def rects_around(self, pos):
        rects = []
    
        for tile in self.tiles_around(pos):
            rects.append(pygame.Rect(int(tile[0]), int(tile[1]), 16, 16))
        return rects

    def render(self, surf, offset=(0,0)):
        for tile in sorted(self.tilemap, key = lambda t: (self.tilemap[t]['layer'], self.tilemap[t]['type'] != 'foliage')):
            img = self.assets[self.tilemap[tile]['type']][self.tilemap[tile]['index']]

            surf.blit(pygame.transform.flip(img, self.tilemap[tile]['flipped_x'], self.tilemap[tile]['flipped_y']), (self.tilemap[tile]['pos'][0] - offset[0], self.tilemap[tile]['pos'][1] - offset[1]))
