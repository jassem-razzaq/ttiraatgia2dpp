import os
import sys
import math
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Crate, Spring
from scripts.tilemap import Tilemap
from scripts.portal import Portal

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Portal Puzzle')
        self.screen = pygame.display.set_mode((960, 640))
        self.display = pygame.Surface((540, 380), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((540, 380))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        
        # Load noportalzone image and make it transparent
        noportalzone_large_img = load_image('tiles/noportalzone.png')
        noportalzone_large_img.set_alpha(128)  # Make it semi-transparent
        noportalzone_img = pygame.transform.scale(noportalzone_large_img, (16, 16))
        
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'noportalzone': [noportalzone_img],  # Single-item list for consistency
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'box': load_image('entities/box.png'),
            'background': pygame.transform.scale(load_image('background.png'), (self.display_2.get_width(), self.display_2.get_height())),
        }
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)
        
        # Portal system
        self.player_portal = Portal(size=64)
        self.cursor_portal = Portal(size=64)
        self.mouse_pos = [0, 0]
        
        # Game elements
        self.crates = []
        self.buttons = []
        self.springs = []
        self.lasers = []
        self.exit_door = None
        self.exit_open = False
        
        self.level = 0
        self.load_level(self.level)
        
        self.scroll = [0, 0]
        self.dead = 0
        self.won = False
        
    def load_level(self, map_id):
        # Get the game directory
        game_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(game_dir, 'data', 'maps', str(map_id) + '.json')
        self.tilemap.load(map_path)
        
        # Reset portals
        self.player_portal.unlock()
        self.cursor_portal.unlock()
        
        # Extract spawners
        self.crates = []
        self.buttons = []
        self.springs = []
        self.lasers = []
        self.exit_door = None
        self.exit_open = False
        
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), 
                                             ('spawners', 3), ('spawners', 6), ('spawners', 7)]):
            variant = spawner['variant']
            pos = spawner['pos']
            
            if variant == 0:  # Player spawn
                self.player.pos = pos
                self.player.air_time = 0
                self.player.velocity = [0, 0]
            elif variant == 1:  # Crate spawn
                self.crates.append(Crate(self, pos))
            elif variant == 2:  # Button
                self.buttons.append({'pos': pos, 'size': (16, 8), 'pressed': False})
            elif variant == 3:  # Spring (bottom attached, launches upward)
                self.springs.append(Spring(self, pos))
            elif variant == 6:  # Laser
                self.lasers.append({'pos': pos, 'size': (16, 240), 'active': True})
            elif variant == 7:  # Exit door
                self.exit_door = {'pos': pos, 'size': (16, 32)}
        
        self.scroll = [0, 0]
        self.dead = 0
        self.won = False
    
    def is_in_noportalzone(self, pos):
        """Check if a position is over a noportalzone tile"""
        tile_loc = str(int(pos[0] // self.tilemap.tile_size)) + ';' + str(int(pos[1] // self.tilemap.tile_size))
        if tile_loc in self.tilemap.tilemap:
            if self.tilemap.tilemap[tile_loc]['type'] == 'noportalzone':
                return True
        return False
    
    def check_portal_teleport(self, entity):
        """Check if entity should be teleported through portals"""
        if not hasattr(entity, 'last_pos'):
            entity.last_pos = entity.pos.copy()
        
        entity_rect = entity.rect()
        last_rect = pygame.Rect(entity.last_pos[0], entity.last_pos[1], entity.size[0], entity.size[1])
        
        # Check player portal
        if self.player_portal.locked and self.cursor_portal.locked:
            collision_result = self.player_portal.check_collision(entity_rect, last_rect)
            if collision_result:
                edge, relative_position = collision_result
                if self.player_portal.teleport_entity(entity, self.cursor_portal, edge, relative_position):
                    # last_pos is updated inside teleport_entity to prevent immediate re-teleport
                    return True
            
            # Check cursor portal
            collision_result = self.cursor_portal.check_collision(entity_rect, last_rect)
            if collision_result:
                edge, relative_position = collision_result
                if self.cursor_portal.teleport_entity(entity, self.player_portal, edge, relative_position):
                    # last_pos is updated inside teleport_entity to prevent immediate re-teleport
                    return True
        
        entity.last_pos = entity.pos.copy()
        return False
    
    def run(self):
        try:
            game_dir = os.path.dirname(os.path.abspath(__file__))
            music_path = os.path.join(game_dir, 'data', 'music.wav')
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except:
            pass  # Music file might not exist
        
        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))
            
            # Update mouse position (scaled to display size)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.mouse_pos[0] = (mouse_x / self.screen.get_width()) * self.display.get_width() + self.scroll[0]
            self.mouse_pos[1] = (mouse_y / self.screen.get_height()) * self.display.get_height() + self.scroll[1]
            
            # Update portals
            self.player_portal.update(self.player.rect().center)
            self.cursor_portal.update(self.mouse_pos)
            
            # Check if cursor or cursor portal is over a noportalzone tile
            cursor_in_noportalzone = self.is_in_noportalzone(self.mouse_pos)
            cursor_portal_center = (self.cursor_portal.pos[0] + self.cursor_portal.size // 2, 
                                    self.cursor_portal.pos[1] + self.cursor_portal.size // 2)
            cursor_portal_in_noportalzone = self.is_in_noportalzone(cursor_portal_center)
            portal_placement_blocked = cursor_in_noportalzone or cursor_portal_in_noportalzone
            
            # Check button presses
            for button in self.buttons:
                button['pressed'] = False
                button_rect = pygame.Rect(button['pos'][0], button['pos'][1], button['size'][0], button['size'][1])
                
                # Check player
                if button_rect.colliderect(self.player.rect()):
                    button['pressed'] = True
            
            # Check if all buttons are pressed (open exit)
            self.exit_open = all(button['pressed'] for button in self.buttons) if self.buttons else False
            
            # Update springs (check for pushing before updating)
            for spring in self.springs:
                # Check if player is pushing the spring horizontally
                if not self.dead:
                    player_rect = self.player.rect()
                    spring_rect = spring.rect()
                    
                    # Check if player is colliding with spring and moving horizontally
                    if player_rect.colliderect(spring_rect):
                        player_horizontal_movement = (self.movement[1] - self.movement[0])
                        
                        # Simple pushing: if player is moving left/right and colliding, move spring directly
                        if player_horizontal_movement > 0:  # Player moving right
                            # Check if player is on the left side of spring
                            if player_rect.centerx < spring_rect.centerx:
                                spring.pos[0] += abs(player_horizontal_movement) * 2  # Move spring right
                        elif player_horizontal_movement < 0:  # Player moving left
                            # Check if player is on the right side of spring
                            if player_rect.centerx > spring_rect.centerx:
                                spring.pos[0] -= abs(player_horizontal_movement) * 2  # Move spring left
                
                # Update spring with physics and collision detection
                entities_to_check = [self.player] + self.crates
                if not spring.teleported_this_frame:
                    spring.update(self.tilemap, entities_to_check)
                    # Check portal teleport for springs
                    if self.check_portal_teleport(spring):
                        spring.teleported_this_frame = True
                else:
                    spring.teleported_this_frame = False
            
            # Check laser collisions
            for laser in self.lasers:
                if not laser['active']:
                    continue
                laser_rect = pygame.Rect(laser['pos'][0], laser['pos'][1], laser['size'][0], laser['size'][1])
                if laser_rect.colliderect(self.player.rect()):
                    self.dead = 1
            
            # Camera is static (no player tracking)
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # Render tilemap
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Update crates (check for pushing before updating)
            for crate in self.crates:
                # Check if player is pushing the crate
                if not self.dead:
                    player_rect = self.player.rect()
                    crate_rect = crate.rect()
                    
                    # Check if player is colliding with crate and moving horizontally
                    if player_rect.colliderect(crate_rect):
                        player_horizontal_movement = (self.movement[1] - self.movement[0])
                        
                        # Simple pushing: if player is moving left/right and colliding, move crate directly
                        if player_horizontal_movement > 0:  # Player moving right
                            # Check if player is on the left side of crate
                            if player_rect.centerx < crate_rect.centerx:
                                crate.pos[0] += abs(player_horizontal_movement) * 2  # Move crate right
                        elif player_horizontal_movement < 0:  # Player moving left
                            # Check if player is on the right side of crate
                            if player_rect.centerx > crate_rect.centerx:
                                crate.pos[0] -= abs(player_horizontal_movement) * 2  # Move crate left
                
                # Update crate with gravity (but no movement input)
                if not crate.teleported_this_frame:
                    crate.update(self.tilemap, movement=(0, 0))
                    # Check portal teleport for crates
                    if self.check_portal_teleport(crate):
                        crate.teleported_this_frame = True
                else:
                    crate.teleported_this_frame = False
            
            # Update player (with crates as colliders for collision detection)
            if not self.dead:
                if not self.player.teleported_this_frame:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0), additional_colliders=self.crates)
                    # Check portal teleport for player
                    if self.check_portal_teleport(self.player):
                        self.player.teleported_this_frame = True
                else:
                    self.player.teleported_this_frame = False
            
            # Render crates
            for crate in self.crates:
                crate.render(self.display, offset=render_scroll)
            
            # Render player
            if not self.dead:
                self.player.render(self.display, offset=render_scroll)
            
            # Render game elements
            # Buttons
            for button in self.buttons:
                button_rect = pygame.Rect(button['pos'][0] - render_scroll[0], 
                                         button['pos'][1] - render_scroll[1], 
                                         button['size'][0], button['size'][1])
                color = (0, 255, 0) if button['pressed'] else (255, 0, 0)
                pygame.draw.rect(self.display, color, button_rect)
            
            # Springs
            for spring in self.springs:
                spring.render(self.display, offset=render_scroll)
            
            # Lasers
            for laser in self.lasers:
                if laser['active']:
                    laser_rect = pygame.Rect(laser['pos'][0] - render_scroll[0], 
                                            laser['pos'][1] - render_scroll[1], 
                                            laser['size'][0], laser['size'][1])
                    pygame.draw.rect(self.display, (255, 0, 0), laser_rect)
            
            # Exit door
            if self.exit_door:
                exit_rect = pygame.Rect(self.exit_door['pos'][0] - render_scroll[0], 
                                      self.exit_door['pos'][1] - render_scroll[1], 
                                      self.exit_door['size'][0], self.exit_door['size'][1])
                color = (0, 255, 0) if self.exit_open else (100, 100, 100)
                pygame.draw.rect(self.display, color, exit_rect)
                
                # Check if player reached exit
                if self.exit_open and exit_rect.colliderect(self.player.rect()):
                    self.won = True
            
            # Render portals
            self.player_portal.render(self.display, offset=render_scroll)
            self.cursor_portal.render(self.display, offset=render_scroll)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_SPACE:
                        if self.player.jump():
                            pass
                    if event.key == pygame.K_r:
                        # Restart level
                        self.load_level(self.level)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Block portal placement if cursor or cursor portal is over noportalzone
                    if portal_placement_blocked:
                        pass  # Do nothing, portal placement is disabled
                    elif event.button == 1:  # Left click
                        if not self.player_portal.locked:
                            self.player_portal.lock('left')
                            self.cursor_portal.lock('left')
                        else:
                            self.player_portal.unlock()
                            self.cursor_portal.unlock()
                    elif event.button == 3:  # Right click
                        if not self.player_portal.locked:
                            self.player_portal.lock('right')
                            self.cursor_portal.lock('right')
                        else:
                            self.player_portal.unlock()
                            self.cursor_portal.unlock()
            
            # Handle death
            if self.dead:
                self.dead += 1
                if self.dead > 60:
                    self.load_level(self.level)
            
            # Handle win
            if self.won:
                game_dir = os.path.dirname(os.path.abspath(__file__))
                maps_dir = os.path.join(game_dir, 'data', 'maps')
                max_level = len([f for f in os.listdir(maps_dir) if f.endswith('.json')]) - 1
                self.level = min(self.level + 1, max_level)
                self.load_level(self.level)
            
            self.display_2.blit(self.display, (0, 0))
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()
