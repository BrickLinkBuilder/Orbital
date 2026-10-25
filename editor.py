import sys
import json

import pygame
from config import *
from assets import *

class Editor:
    def __init__(self):

        pygame.init()

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((1200, 900))
        self.display = pygame.Surface((600, 450), pygame.SRCALPHA)
        self.border_surf = pygame.Surface((120, 200), pygame.SRCALPHA)
        self.ui_surf = pygame.Surface((400, 300), pygame.SRCALPHA)
        self.img_surf = pygame.Surface((16, 16))
        self.font = pygame.font.Font('font.ttf', 16)

        self.assets = images()

        self.tilemap = {}
        self.groups = list(self.assets.keys())
        self.group_index = 1
        self.map = 0
        self.img_index = 0
        self.layer = 0
        self.tile_size = 16
        self.on_grid = True
        self.clicking = False
        self.erasing = False
        self.offset = [0, 0]
        self.flips = [False, False]
        self.cam_movement = [False, False, False, False]
        self.cam_speed = 3
        self.filling = False
        self.selecting = False
        self.start_pos = (0, 0)
        self.current_pos = (0, 0)
        self.box_frozen = False
        self.show_grid = True
        self.deleting = False
        
    def autotile(self):
        for tile in self.tilemap:
            t_layer = self.tilemap[tile]['layer']
            pos = [int(self.tilemap[tile]['pos'][0]), int(self.tilemap[tile]['pos'][1])]

            if t_layer == self.layer and self.tilemap[tile]['type'] == 'tiles':
                right = (str(int(pos[0]) + 1 * 16) + ';' +  str(int(pos[1])) + ';' + str(t_layer))
                if right in self.tilemap:
                    right = right if self.tilemap[right]['layer'] == self.layer else 0

                left = (str(int(pos[0]) - 1 * 16) + ';' +  str(int(pos[1])) + ';' + str(t_layer))
                if left in self.tilemap:
                    left = left if self.tilemap[left]['layer'] == self.layer else 0

                top = (str(int(pos[0])) + ';' +  str(int(pos[1]) - 1 * 16) + ';' + str(t_layer))
                if top in self.tilemap:
                    top = top if self.tilemap[top]['layer'] == self.layer else 0

                bottom = (str(int(pos[0])) + ';' +  str(int(pos[1]) + 1 * 16) + ';' + str(t_layer))
                if bottom in self.tilemap:
                    bottom = bottom if self.tilemap[bottom]['layer'] == self.layer else 0

                if right in self.tilemap and bottom in self.tilemap:
                    if top not in self.tilemap and left not in self.tilemap:
                        self.tilemap[tile]['index'] = 0

                if right in self.tilemap and left in self.tilemap and bottom in self.tilemap:
                    if top not in self.tilemap:
                        self.tilemap[tile]['index'] = 1

                if left in self.tilemap and bottom in self.tilemap:
                    if top not in self.tilemap and right not in self.tilemap:
                        self.tilemap[tile]['index'] = 2

                if right in self.tilemap and top in self.tilemap and bottom in self.tilemap:
                    if left not in self.tilemap:
                        self.tilemap[tile]['index'] = 3

                if right in self.tilemap and top in self.tilemap and left in self.tilemap and bottom in self.tilemap:
                    self.tilemap[tile]['index'] = 4

                if left in self.tilemap and top in self.tilemap and bottom in self.tilemap:
                    if right not in self.tilemap:
                        self.tilemap[tile]['index'] = 5

                if right in self.tilemap and top in self.tilemap:
                    if bottom not in self.tilemap and left not in self.tilemap:
                        self.tilemap[tile]['index'] = 6

                if right in self.tilemap and left in self.tilemap and top in self.tilemap:
                    if bottom not in self.tilemap:
                        self.tilemap[tile]['index'] = 7

                if left in self.tilemap and top in self.tilemap:
                    if bottom not in self.tilemap and right not in self.tilemap:
                        self.tilemap[tile]['index'] = 8        

    def update(self):
        while True:
            self.ui_surf.fill((0, 0, 0, 0))
            self.display.fill((0, 0, 0))

            draw_grid(self.display, 16, self.offset)

            self.offset[0] += int(self.cam_movement[0] - self.cam_movement[1]) * 4
            self.offset[1] += int(self.cam_movement[3] - self.cam_movement[2]) * 4

            self.mpos = pygame.mouse.get_pos()
            self.mpos = (self.mpos[0] / 2, self.mpos[1] / 2)

            if self.on_grid:
                self.mpos = (int((self.mpos[0] + self.offset[0]) // self.tile_size), int((self.mpos[1] + self.offset[1]) // self.tile_size))
            else:
                self.mpos = (int(self.mpos[0] + self.offset[0]), int(self.mpos[1] + self.offset[1]))
            
            self.preview_pos = (self.mpos[0] * self.tile_size - self.offset[0], self.mpos[1] * self.tile_size - self.offset[1])

            preview_img = self.assets[self.groups[self.group_index]][self.img_index].copy()
            preview_img.set_alpha(100)

            if self.on_grid:
                self.display.blit(pygame.transform.flip(preview_img, self.flips[0], self.flips[1]), self.preview_pos)
            else:
                self.display.blit(pygame.transform.flip(preview_img, self.flips[0], self.flips[1]), (self.mpos[0] - self.offset[0], self.mpos[1] - self.offset[1]))

            if self.clicking:
                if self.on_grid:
                    self.tilemap[str(int(self.mpos[0] * 16)) + ';' + str(int(self.mpos[1] * 16)) + ';' + str(self.layer)] = {'type' : self.groups[self.group_index], 'index' : self.img_index, 'flipped_x' : self.flips[0], 'flipped_y' : self.flips[1], 'pos' : (self.mpos[0] * 16, self.mpos[1] * 16), 'layer' : self.layer}
                else:
                    self.clicking = False
                    self.tilemap[str(int(self.mpos[0])) + ';' + str(int(self.mpos[1])) + ';' + str(self.layer)] = {'type' : self.groups[self.group_index], 'index' : self.img_index, 'flipped_x' : self.flips[0], 'flipped_y' : self.flips[1], 'pos' : (self.mpos[0], self.mpos[1]), 'layer' : self.layer}

            for tile in sorted(self.tilemap, key=lambda t: (self.tilemap[t]['layer'], self.tilemap[t]['type'] != 'foliage')):                
                
                img = self.assets[self.tilemap[tile]['type']][self.tilemap[tile]['index']]
                
                if self.tilemap[tile]['layer'] == self.layer or self.layer == 0:
                    self.display.blit(img, (self.tilemap[tile]['pos'][0] - self.offset[0], self.tilemap[tile]['pos'][1] - self.offset[1]))
                else:
                    img = img.copy()
                    img.set_alpha(128)
                    self.display.blit(img, (self.tilemap[tile]['pos'][0] - self.offset[0], self.tilemap[tile]['pos'][1] - self.offset[1]))

                if self.erasing:
                    if self.tilemap[tile]['pos'] == (self.mpos[0] * 16, self.mpos[1] * 16) and self.tilemap[tile]['layer'] == self.layer:
                        del self.tilemap[tile]

            self.filling = False
            self.deleting = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not self.selecting:
                        self.clicking = True
                    if event.button == 1 and self.selecting:
                        self.clicking = False
                        self.box_frozen = True
                    if event.button == 3:
                        self.erasing = True
                    if event.button == 4:
                        self.img_index = (self.img_index + 1) % len(self.assets[self.groups[self.group_index]])
                    if event.button == 5:
                        self.img_index = (self.img_index - 1) % len(self.assets[self.groups[self.group_index]])
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.erasing = False
                if event.type == pygame.MOUSEMOTION and self.selecting and not self.box_frozen:
                    self.current_pos = (event.pos[0] / 2, event.pos[1] / 2)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d:
                        self.cam_movement[0] = True
                    if event.key == pygame.K_a:
                        self.cam_movement[1] = True
                    if event.key == pygame.K_w:
                        self.cam_movement[2] = True
                    if event.key == pygame.K_s:
                        self.cam_movement[3] = True
                    if event.key == pygame.K_g:
                        self.on_grid = not self.on_grid
                    if event.key == pygame.K_x:
                        self.flips[0] = not self.flips[0]
                    if event.key == pygame.K_y:
                        self.flips[1] = not self.flips[1]
                    if event.key == pygame.K_EQUALS:
                        self.layer += 1
                    if event.key == pygame.K_MINUS and self.layer > 0:
                        self.layer -= 1
                    if event.key == pygame.K_h:
                        self.img_index = 0
                        self.group_index = (self.group_index + 1) % len(self.groups)
                    if event.key == pygame.K_i:
                        save_tilemap(str(self.map), self.tilemap)
                    if event.key == pygame.K_l:
                        self.tilemap = load_tilemap(str(self.map), self.tilemap)
                    if event.key == pygame.K_t:
                        self.autotile()
                    if event.key == pygame.K_c:
                        self.selecting = not self.selecting
                        if self.selecting:
                            self.box_frozen = False
                            mpos = pygame.mouse.get_pos()
                            self.start_pos = (mpos[0] / 2, mpos[1] / 2)
                            self.current_pos = self.start_pos
                        else:
                            self.box_frozen = False  
                    if event.key == pygame.K_f:
                        self.filling = True
                    if event.key == pygame.K_BACKSPACE:
                        self.deleting = True
                    if event.key == pygame.K_RIGHTBRACKET:
                        self.map += 1
                    if event.key == pygame.K_LEFTBRACKET:
                        self.map -= 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_d:
                        self.cam_movement[0] = False
                    if event.key == pygame.K_a:
                        self.cam_movement[1] = False
                    if event.key == pygame.K_w:
                        self.cam_movement[2] = False
                    if event.key == pygame.K_s:
                        self.cam_movement[3] = False

            if self.selecting or self.box_frozen:
                x1, y1 = self.start_pos
                x2, y2 = self.current_pos
                rect_x = min(x1, x2)
                rect_y = min(y1, y2)
                rect_w = abs(x1 - x2)
                rect_h = abs(y1 - y2)
                box = pygame.draw.rect(self.display, (255,255,0), (rect_x, rect_y, rect_w, rect_h), 2)
                for tile in self.tilemap.copy():
                    img = self.assets[self.tilemap[tile]['type']][self.tilemap[tile]['index']]
                
                    t_rect = pygame.Rect(self.tilemap[tile]['pos'][0], self.tilemap[tile]['pos'][1], img.get_width(), img.get_height())
                                                    
                    if t_rect.colliderect(box) and self.deleting and self.tilemap[tile]['layer'] == self.layer:
                        del self.tilemap[tile]
            
                    if t_rect.colliderect(box) and self.filling and self.tilemap[tile]['layer'] == self.layer:
                        fill(self.mpos, self.tilemap, self.layer, self.img_index, self.groups[self.group_index], self.tile_size)
            

            render_txt("Layer: " + str(self.layer), (355, 0), self.font, self.ui_surf)
            render_txt("Pos: " + str(self.mpos[0]) + ":" + str(self.mpos[1]), (355, 10), self.font, self.ui_surf)
            render_txt("Group: " + str(self.groups[self.group_index]), (10, 0), self.font, self.ui_surf)
            render_txt("Fhori: " + str(self.flips[0]), (355, 20), self.font, self.ui_surf)
            render_txt("Fver: " + str(self.flips[1]), (355, 30), self.font, self.ui_surf)
            render_txt("Ogrid: " + str(self.on_grid), (355, 40), self.font, self.ui_surf)
            render_txt("Map: " + str(self.map), (355, 50), self.font, self.ui_surf)
            render_txt("TCount: " + str(len(self.tilemap)), (355, 60), self.font, self.ui_surf)

            for index, img in enumerate(self.assets[self.groups[self.group_index]]):
                row = index % 3 
                col = index // 3 
                og_img = img
                if self.groups[self.group_index] != 'tiles':
                    img = pygame.transform.scale(img, (16, 16))
                else:
                    img = og_img
                self.ui_surf.blit(img, (row * 16 + 10, col * 16 + 32))

            self.border_surf.fill((0, 0, 128, 50))
            self.display.blit(self.border_surf, (0, 0))
            pygame.draw.rect(self.display, (0, 0, 128), (0, 0, 120, 200), 1)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0,0))
            self.screen.blit(pygame.transform.scale(self.ui_surf, self.screen.get_size()), (0,0))    

            pygame.display.update()
            self.clock.tick(60)

Editor().update()