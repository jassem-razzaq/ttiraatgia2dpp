import os
import sys

import pygame

from scripts.utils import load_images, load_image
from scripts.tilemap import Tilemap

class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('editor')
        self.screen = pygame.display.set_mode((960, 640))
        self.display = pygame.Surface((540, 380))
        
        # Calculate scale factors for mouse position conversion
        self.scale_x = self.screen.get_width() / self.display.get_width()
        self.scale_y = self.screen.get_height() / self.display.get_height()

        self.clock = pygame.time.Clock()
        
        # Load noportalzone image and make it transparent
        noportalzone_large_img = load_image('tiles/noportalzone.png')
        noportalzone_large_img.set_alpha(128)  # Make it semi-transparent
        noportalzone_img = pygame.transform.scale(noportalzone_large_img, (16, 16))

        door_large_img = load_image('tiles/door.png')
        door = pygame.transform.scale(door_large_img, (48, 48))

        key_large_img = load_image('tiles/key.png')
        key = pygame.transform.scale(key_large_img, (48, 48))

        # Load spikes image and scale to full width, half height (16x8 for 16x16 tile)
        spikes_large_img = load_image('spikes.png')
        spikes_img = pygame.transform.scale(spikes_large_img, (16, 8))
        
        # Load spring_horizontal image for horizontal launcher tile
        game_dir = os.path.dirname(os.path.abspath(__file__))
        spring_horizontal_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'spring_horizontal.png')).convert_alpha()
        
        # Load spring with alpha transparency
        spring_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'spring.png')).convert_alpha()
        
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'noportalzone': [noportalzone_img],  # Single-item list for consistency
            'spikes': [spikes_img],  # Single-item list, half tile size
            'spring_horizontal': [spring_horizontal_img],  # Horizontal spring launcher tile
            'spawners': load_images('tiles/spawners'),
            'box': [load_image('entities/box.png')],  # Box as a single-item list for consistency
            'spring': [spring_img],
            'door': [door],
            'key': [key],
        }
        
        self.movement = [False, False, False, False]
        
        self.tilemap = Tilemap(self, tile_size=16)
        
        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass
        
        self.scroll = [0, 0]
        
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.tile_rotation = 0  # Rotation in degrees (0, 90, 180, 270)
        
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True
        
    def run(self):
        while True:
            self.display.fill((0, 0, 0))
            
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Render boxes, springs, doors, and keys from offgrid tiles
            for tile in self.tilemap.offgrid_tiles:
                if tile['type'] == 'spawners':
                    if tile['variant'] == 1:  # Box
                        box_img = self.assets['box'][0]
                        self.display.blit(box_img, (tile['pos'][0] - render_scroll[0], tile['pos'][1] - render_scroll[1]))
                    elif tile['variant'] == 3:  # Spring (bottom attached)
                        spring_img = self.assets['spring'][0].copy()
                        # Use spring image as-is without scaling
                        self.display.blit(spring_img, (tile['pos'][0] - render_scroll[0], tile['pos'][1] - render_scroll[1]))
                elif tile['type'] in ['door', 'key']:
                    # Door and key are already centered in their position
                    tile_img = self.assets[tile['type']][0]
                    self.display.blit(tile_img, (tile['pos'][0] - render_scroll[0], tile['pos'][1] - render_scroll[1]))
            
            # Handle box, spring, and spikes separately since they're single images, not lists
            if self.tile_list[self.tile_group] == 'box':
                current_tile_img = self.assets['box'][0].copy()
            elif self.tile_list[self.tile_group] == 'spring':
                current_tile_img = self.assets['spring'][0].copy()
                # Use spring image as-is without scaling
            elif self.tile_list[self.tile_group] == 'spikes':
                current_tile_img = self.assets['spikes'][0].copy()
                # Apply rotation if any
                if self.tile_rotation != 0:
                    current_tile_img = pygame.transform.rotate(current_tile_img, -self.tile_rotation)
            elif self.tile_list[self.tile_group] in ['door', 'key']:
                current_tile_img = self.assets[self.tile_list[self.tile_group]][0].copy()
            else:
                current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)
            
            mpos = pygame.mouse.get_pos()
            # Convert mouse position from screen coordinates to display coordinates
            mpos = (mpos[0] / self.scale_x, mpos[1] / self.scale_y)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            if self.ongrid:
                if self.tile_list[self.tile_group] == 'spikes':
                    # Position spike in the appropriate half of the tile based on rotation
                    # Spikes fill full width (16) and half height (8)
                    tile_x = tile_pos[0] * self.tilemap.tile_size - self.scroll[0]
                    tile_y = tile_pos[1] * self.tilemap.tile_size - self.scroll[1]
                    
                    if self.tile_rotation == 0:  # Pointing up (bottom half, full width)
                        spike_pos = (tile_x, tile_y + 8)
                    elif self.tile_rotation == 90:  # Pointing right (left half, full height when rotated)
                        spike_pos = (tile_x, tile_y)
                    elif self.tile_rotation == 180:  # Pointing down (top half, full width)
                        spike_pos = (tile_x, tile_y)
                    elif self.tile_rotation == 270:  # Pointing left (right half, full height when rotated)
                        spike_pos = (tile_x + 8, tile_y)
                    else:
                        spike_pos = (tile_x, tile_y + 8)  # Default bottom half
                    
                    self.display.blit(current_tile_img, spike_pos)
                elif self.tile_list[self.tile_group] in ['door', 'key']:
                    # Center door and key on the tile (they're 48x48, tiles are 16x16)
                    tile_x = tile_pos[0] * self.tilemap.tile_size - self.scroll[0]
                    tile_y = tile_pos[1] * self.tilemap.tile_size - self.scroll[1]
                    # Center the 48x48 image on the 16x16 tile
                    offset_x = (self.tilemap.tile_size - current_tile_img.get_width()) // 2
                    offset_y = (self.tilemap.tile_size - current_tile_img.get_height()) // 2
                    self.display.blit(current_tile_img, (tile_x + offset_x, tile_y + offset_y))
                else:
                    self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                # For offgrid placement, center door and key on cursor
                if self.tile_list[self.tile_group] in ['door', 'key']:
                    self.display.blit(current_tile_img, (mpos[0] - current_tile_img.get_width() // 2, mpos[1] - current_tile_img.get_height() // 2))
                else:
                    self.display.blit(current_tile_img, mpos)
            
            if self.clicking and self.ongrid:
                # Box is placed as a spawner variant 1 (crate spawner) in offgrid
                if self.tile_list[self.tile_group] == 'box':
                    self.tilemap.offgrid_tiles.append({'type': 'spawners', 'variant': 1, 'pos': (tile_pos[0] * self.tilemap.tile_size, tile_pos[1] * self.tilemap.tile_size)})
                elif self.tile_list[self.tile_group] == 'spring':
                    # Spring variant 3 (bottom attached, launches upward)
                    self.tilemap.offgrid_tiles.append({'type': 'spawners', 'variant': 3, 'pos': (tile_pos[0] * self.tilemap.tile_size, tile_pos[1] * self.tilemap.tile_size)})
                elif self.tile_list[self.tile_group] == 'spikes':
                    # Spikes tile with rotation
                    self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': 'spikes', 'variant': 0, 'pos': tile_pos, 'rotation': self.tile_rotation}
                elif self.tile_list[self.tile_group] in ['door', 'key']:
                    # Door and key are placed as offgrid tiles, centered on the tile
                    tile_img = self.assets[self.tile_list[self.tile_group]][0]
                    tile_x = tile_pos[0] * self.tilemap.tile_size
                    tile_y = tile_pos[1] * self.tilemap.tile_size
                    # Center the 48x48 image on the 16x16 tile
                    offset_x = (self.tilemap.tile_size - tile_img.get_width()) // 2
                    offset_y = (self.tilemap.tile_size - tile_img.get_height()) // 2
                    centered_pos = (tile_x + offset_x, tile_y + offset_y)
                    self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': 0, 'pos': centered_pos})
                else:
                    self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    # Handle box and spring rendering
                    if tile['type'] == 'spawners':
                        if tile['variant'] == 1:  # Box
                            tile_img = self.assets['box'][0]
                        elif tile['variant'] == 3:  # Spring
                            tile_img = self.assets['spring'][0]
                            tile_img = pygame.transform.scale(tile_img, (4, 8))
                        else:
                            tile_img = self.assets['spawners'][tile['variant']]
                    else:
                        tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
            
            self.display.blit(current_tile_img, (5, 5))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            # Box is placed as a spawner variant 1 (crate spawner) in offgrid
                            if self.tile_list[self.tile_group] == 'box':
                                self.tilemap.offgrid_tiles.append({'type': 'spawners', 'variant': 1, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                            elif self.tile_list[self.tile_group] == 'spring':
                                # Spring variant 3 (bottom attached, launches upward)
                                self.tilemap.offgrid_tiles.append({'type': 'spawners', 'variant': 3, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                            elif self.tile_list[self.tile_group] in ['door', 'key']:
                                # Center door and key on cursor position
                                tile_img = self.assets[self.tile_list[self.tile_group]][0]
                                centered_pos = (mpos[0] + self.scroll[0] - tile_img.get_width() // 2, mpos[1] + self.scroll[1] - tile_img.get_height() // 2)
                                self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': 0, 'pos': centered_pos})
                            else:
                                self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if self.tile_list[self.tile_group] not in ['box', 'spring', 'noportalzone', 'spikes', 'spring_horizontal']:  # Box, spring, noportalzone, spikes, and spring_horizontal have special handling
                            if event.button == 4:
                                self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                            if event.button == 5:
                                self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                        # Spring, noportalzone, and spikes no longer have variants - removed
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                            self.tile_rotation = 0  # Reset rotation when switching tiles
                            # If switching to spring, noportalzone, spikes, or spring_horizontal, ensure variant is valid
                            if self.tile_list[self.tile_group] in ['spring', 'noportalzone', 'spikes', 'spring_horizontal']:
                                self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                            self.tile_rotation = 0  # Reset rotation when switching tiles
                            # If switching to spring, noportalzone, spikes, or spring_horizontal, ensure variant is valid
                            if self.tile_list[self.tile_group] in ['spring', 'noportalzone', 'spikes', 'spring_horizontal']:
                                self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save('map.json')
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_r:
                        # Rotate tile (only for tiles that support rotation like spikes)
                        if self.tile_list[self.tile_group] == 'spikes':
                            self.tile_rotation = (self.tile_rotation + 90) % 360
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
            
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Editor().run()