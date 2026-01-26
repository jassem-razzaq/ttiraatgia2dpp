import os
import sys
import math
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Crate, Spring
from scripts.tilemap import Tilemap, PHYSICS_TILES
from scripts.portal import Portal


class Game:
    def __init__(self, level_path=None):
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

        door = load_image('tiles/door.png')

        key_large_img = load_image('tiles/key.png')
        key = pygame.transform.scale(key_large_img, (48, 48))

        # Load spikes image and scale to full width, half height (16x8 for 16x16 tile)
        spikes_large_img = load_image('spikes.png')
        spikes_img = pygame.transform.scale(spikes_large_img, (16, 8))

        # Load spring_horizontal image for horizontal launcher tile
        game_dir = os.path.dirname(os.path.abspath(__file__))
        spring_horizontal_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'spring_horizontal.png')).convert_alpha()

        # Load cursor image
        cursor_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'cursor.png'))
        cursor_img = cursor_img.convert_alpha()

        # Load control images
        left_mouse_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'controls', 'left_mouse.png')).convert_alpha()
        right_mouse_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'controls', 'right_mouse.png')).convert_alpha()
        a_button_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'controls', 'a_button.png')).convert_alpha()
        d_button_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'controls', 'd_button.png')).convert_alpha()
        w_button_img = pygame.image.load(os.path.join(game_dir, 'data', 'images', 'controls', 'w_button.png')).convert_alpha()
        scale_factor = 0.75
        a_button_img = pygame.transform.scale(a_button_img, (int(a_button_img.get_width() * scale_factor), int(a_button_img.get_height() * scale_factor)))
        d_button_img = pygame.transform.scale(d_button_img, (int(d_button_img.get_width() * scale_factor), int(d_button_img.get_height() * scale_factor)))
        w_button_img = pygame.transform.scale(w_button_img, (int(w_button_img.get_width() * scale_factor), int(w_button_img.get_height() * scale_factor)))
        
        self.control_images = [left_mouse_img, right_mouse_img]

        # Load portal sprites
        portal_red_images = load_images('portal_red')
        portal_white_images = load_images('portal_white')
        portal_grey_images = load_images('portal_grey')

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'noportalzone': [noportalzone_img],  # Single-item list for consistency
            'spikes': [spikes_img],  # Single-item list, half tile size
            'spring_horizontal': [spring_horizontal_img],  # Horizontal spring launcher tile
            'portal/red': Animation(portal_red_images, img_dur=5),
            'portal/white': Animation(portal_white_images, img_dur=5),
            'portal/grey': Animation(portal_grey_images, img_dur=5),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'box': load_image('entities/box.png'),
            'background': pygame.transform.scale(load_image('background2.png'), (self.display_2.get_width(), self.display_2.get_height())),
            'door': [door],
            'key': [key],
            'a_button': [a_button_img],
            'd_button': [d_button_img],
            'w_button': [w_button_img],
            'left_mouse_img': [left_mouse_img],
            'right_mouse_img': [right_mouse_img]
        }

        # Load audio files
        audio_dir = os.path.join(game_dir, 'data', 'audio')
        try:
            jump_sound_path = os.path.join(audio_dir, 'jump.wav')
            if os.path.exists(jump_sound_path):
                self.jump_sound = pygame.mixer.Sound(jump_sound_path)
            else:
                self.jump_sound = None
        except:
            self.jump_sound = None
        
        try:
            death_sound_path = os.path.join(audio_dir, 'death.wav')
            if os.path.exists(death_sound_path):
                self.death_sound = pygame.mixer.Sound(death_sound_path)
            else:
                self.death_sound = None
        except:
            self.death_sound = None
        
        try:
            key_sound_path = os.path.join(audio_dir, 'key.wav')
            if os.path.exists(key_sound_path):
                self.key_sound = pygame.mixer.Sound(key_sound_path)
            else:
                self.key_sound = None
        except:
            self.key_sound = None
        
        try:
            portal_shift_sound_path = os.path.join(audio_dir, 'portal_shift.wav')
            if os.path.exists(portal_shift_sound_path):
                self.portal_shift_sound = pygame.mixer.Sound(portal_shift_sound_path)
            else:
                self.portal_shift_sound = None
        except:
            self.portal_shift_sound = None
        
        try:
            portal_travel_sound_path = os.path.join(audio_dir, 'portal_travel.wav')
            if os.path.exists(portal_travel_sound_path):
                self.portal_travel_sound = pygame.mixer.Sound(portal_travel_sound_path)
            else:
                self.portal_travel_sound = None
        except:
            self.portal_travel_sound = None
        
        try:
            spring_sound_path = os.path.join(audio_dir, 'spring.wav')
            if os.path.exists(spring_sound_path):
                self.spring_sound = pygame.mixer.Sound(spring_sound_path)
            else:
                self.spring_sound = None
        except:
            self.spring_sound = None
        
        try:
            portal_place_sound_path = os.path.join(audio_dir, 'portal_place.wav')
            if os.path.exists(portal_place_sound_path):
                self.portal_place_sound = pygame.mixer.Sound(portal_place_sound_path)
            else:
                self.portal_place_sound = None
        except:
            self.portal_place_sound = None

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self, tile_size=16)

        # Store cursor image and hide default cursor
        self.cursor_img = cursor_img
        pygame.mouse.set_visible(False)

        # Portal system
        self.player_portal = Portal(self, size=64)
        self.cursor_portal = Portal(self, size=64)
        self.mouse_pos = [0, 0]
        self.portal_mode = False  # Track if shift is held (portal mode active)
        self.current_portal_color = None  # 'red' or 'white' when locked

        # Game elements
        self.crates = []
        self.buttons = []
        self.springs = []
        self.exit_door = None
        self.exit_open = False
        self.keys = []  # List of key positions (offgrid tiles)
        self.doors = []  # List of door positions (offgrid tiles)
        self.has_key = False  # Track if player has collected a key

        # Key system
        self.has_key = False  # Whether player has collected the key
        self.room_has_key = False  # Whether the current room has a key

        # Load level from path if provided, otherwise default to level 0
        if level_path is not None:
            self.level = level_path
        else:
            self.level = 0
        self.load_level(self.level)

        self.scroll = [0, 0]
        self.dead = 0
        self.won = False

        # Transition system
        self.transition_active = False
        self.transition_type = None  # 'death' or 'win'
        self.transition_progress = 0  # 0 to 1
        self.transition_duration = 60  # frames for fade in + out
                
        # Win screen system
        self.win_screen_time = 0.0  # Time since win screen appeared
        self.win_screen_duration = 2.0  # Show win screen for 2 seconds

        # Pause system
        self.paused = False
        font_path = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
        self.pause_font = pygame.font.Font(font_path, 12)  # Font for pause menu
        
        # Pause menu buttons
        menu_x = self.display.get_width() // 2 - 70
        menu_y = self.display.get_height() // 2 - 20
        button_width = 140
        button_height = 30
        self.resume_button_rect = pygame.Rect(menu_x, menu_y, button_width, button_height)
        self.quit_button_rect = pygame.Rect(menu_x, menu_y + button_height + 10, button_width, button_height)

    def load_level(self, map_id_or_path):
        # Get the game directory
        game_dir = os.path.dirname(os.path.abspath(__file__))
        # If map_id_or_path is a number or string that's all digits, treat it as map_id
        # Otherwise, treat it as a full path
        if isinstance(map_id_or_path, int):
            map_path = os.path.join(game_dir, 'data', 'maps', str(map_id_or_path) + '.json')
        elif isinstance(map_id_or_path, str) and map_id_or_path.isdigit():
            map_path = os.path.join(game_dir, 'data', 'maps', map_id_or_path + '.json')
        else:
            # It's already a path
            map_path = map_id_or_path

        self.tilemap.load(map_path)

        # Reset portals
        self.player_portal.unlock()
        self.cursor_portal.unlock()
        self.portal_mode = False
        self.current_portal_color = None

        # Extract spawners
        self.crates = []
        self.buttons = []
        self.springs = []
        self.exit_door = None
        self.exit_open = False
        self.keys = []  # List of key positions (offgrid tiles)
        self.doors = []  # List of door positions (offgrid tiles)
        self.has_key = False  # Reset key collection status

        # Reset key system
        self.has_key = False
        self.room_has_key = False

        # Check if room has a key (in tilemap or offgrid)
        for loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[loc]
            if tile['type'] == 'key':
                self.room_has_key = True
                break

        if not self.room_has_key:
            for tile in self.tilemap.offgrid_tiles:
                if tile['type'] == 'key':
                    self.room_has_key = True
                    break

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
            elif variant == 7:  # Exit door
                self.exit_door = {'pos': pos, 'size': (16, 32)}

        # Extract keys and doors from offgrid tiles
        # Note: Keys and doors are stored in offgrid_tiles with their centered positions
        for tile in self.tilemap.offgrid_tiles:
            if tile['type'] == 'key':
                self.keys.append(tile)  # Store the tile directly
            elif tile['type'] == 'door':
                self.doors.append(tile)  # Store the tile directly

        self.scroll = [0, 0]
        self.dead = 0
        self.won = False

        self.tutorial_hints = []
        if (isinstance(map_id_or_path, int) and map_id_or_path == 1) or \
        (isinstance(map_id_or_path, str) and map_id_or_path.endswith('level1.json')):
            # Add control hints at specific world positions
            self.tutorial_hints = [
                {'image': 'a_button', 'pos': (20, 342)},  # Adjust these coordinates
                {'image': 'd_button', 'pos': (40, 342)},
                {'image': 'w_button', 'pos': (73, 325)},
                {'image': 'w_button', 'pos': (234, 85)},
                {'image': 'w_button', 'pos': (170, 125)},
                {'image': 'left_mouse_img', 'pos': (235, 340)},    # Adjust coordinates
                {'image': 'right_mouse_img', 'pos': (468, 20)},
            ]

    def is_in_noportalzone(self, pos):
        """Check if a position is over a noportalzone tile"""
        tile_loc = str(int(pos[0] // self.tilemap.tile_size)) + ';' + str(int(pos[1] // self.tilemap.tile_size))
        if tile_loc in self.tilemap.tilemap:
            if self.tilemap.tilemap[tile_loc]['type'] == 'noportalzone':
                return True
        return False

    def portal_overlaps_noportalzone(self, portal_rect):
        """Check if any part of a portal rectangle overlaps with any noportalzone tile"""
        # Get the tile coordinates that the portal rectangle covers
        min_tile_x = int(portal_rect.left // self.tilemap.tile_size)
        max_tile_x = int(portal_rect.right // self.tilemap.tile_size)
        min_tile_y = int(portal_rect.top // self.tilemap.tile_size)
        max_tile_y = int(portal_rect.bottom // self.tilemap.tile_size)

        # Check all tiles that the portal rectangle could overlap with
        for tile_x in range(min_tile_x, max_tile_x + 1):
            for tile_y in range(min_tile_y, max_tile_y + 1):
                tile_loc = str(tile_x) + ';' + str(tile_y)
                if tile_loc in self.tilemap.tilemap:
                    if self.tilemap.tilemap[tile_loc]['type'] == 'noportalzone':
                        # Check if this tile actually overlaps with the portal rectangle
                        tile_rect = pygame.Rect(
                            tile_x * self.tilemap.tile_size,
                            tile_y * self.tilemap.tile_size,
                            self.tilemap.tile_size,
                            self.tilemap.tile_size
                        )
                        if portal_rect.colliderect(tile_rect):
                            return True
        return False

    def portal_fully_encompassed_by_solid(self, portal_rect):
        """Check if the portal is fully encompassed by grass or stone tiles"""
        # Get the tile coordinates that the portal rectangle covers
        min_tile_x = int(portal_rect.left // self.tilemap.tile_size)
        max_tile_x = int(portal_rect.right // self.tilemap.tile_size)
        min_tile_y = int(portal_rect.top // self.tilemap.tile_size)
        max_tile_y = int(portal_rect.bottom // self.tilemap.tile_size)

        # Check all tiles that the portal rectangle overlaps with
        for tile_x in range(min_tile_x, max_tile_x + 1):
            for tile_y in range(min_tile_y, max_tile_y + 1):
                tile_loc = str(tile_x) + ';' + str(tile_y)
                tile_rect = pygame.Rect(
                    tile_x * self.tilemap.tile_size,
                    tile_y * self.tilemap.tile_size,
                    self.tilemap.tile_size,
                    self.tilemap.tile_size
                )

                # Check if this tile overlaps with the portal
                if portal_rect.colliderect(tile_rect):
                    # If the tile exists and is not grass or stone, portal is not fully encompassed
                    if tile_loc in self.tilemap.tilemap:
                        tile = self.tilemap.tilemap[tile_loc]
                        if tile['type'] not in PHYSICS_TILES:  # Not grass or stone
                            return False
                    else:
                        # If tile doesn't exist (empty space), portal is not fully encompassed
                        return False

        # If we get here, all overlapping tiles are grass or stone
        return True

    def cursor_over_solid_tile(self, pos):
        """Check if the cursor position is directly over a grass or stone tile"""
        tile_loc = str(int(pos[0] // self.tilemap.tile_size)) + ';' + str(int(pos[1] // self.tilemap.tile_size))
        if tile_loc in self.tilemap.tilemap:
            tile_type = self.tilemap.tilemap[tile_loc]['type']
            if tile_type in PHYSICS_TILES:  # PHYSICS_TILES contains 'grass' and 'stone'
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
                    # Play portal travel sound
                    if self.portal_travel_sound:
                        self.portal_travel_sound.play()
                    # last_pos is updated inside teleport_entity to prevent immediate re-teleport
                    return True

            # Check cursor portal
            collision_result = self.cursor_portal.check_collision(entity_rect, last_rect)
            if collision_result:
                edge, relative_position = collision_result
                if self.cursor_portal.teleport_entity(entity, self.player_portal, edge, relative_position):
                    # Play portal travel sound
                    if self.portal_travel_sound:
                        self.portal_travel_sound.play()
                    # last_pos is updated inside teleport_entity to prevent immediate re-teleport
                    return True

        entity.last_pos = entity.pos.copy()
        return False

    def run(self):
        try:
            game_dir = os.path.dirname(os.path.abspath(__file__))
            music_path = os.path.join(game_dir, 'data', 'audio', 'level_music.mp3')
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except:
            pass  # Music file might not exist

        dt = 0.0  # Delta time for frame updates
        while True:
            dt = self.clock.tick(60) / 1000.0  # Get dt from tick
            
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))

            # Update mouse position (scaled to display size)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.mouse_pos[0] = (mouse_x / self.screen.get_width()) * self.display.get_width() + self.scroll[0]
            self.mouse_pos[1] = (mouse_y / self.screen.get_height()) * self.display.get_height() + self.scroll[1]

            # Only update game logic if not paused
            if not self.paused:
                # Update portals
                self.player_portal.update(self.player.rect().center)
                self.cursor_portal.update(self.mouse_pos)

                # Check if cursor or cursor portal overlaps with any noportalzone tile
                cursor_in_noportalzone = self.is_in_noportalzone(self.mouse_pos)
                cursor_portal_rect = self.cursor_portal.get_rect()
                cursor_portal_in_noportalzone = self.portal_overlaps_noportalzone(cursor_portal_rect)
                cursor_portal_encompassed_by_solid = self.portal_fully_encompassed_by_solid(cursor_portal_rect)
                cursor_over_solid = self.cursor_over_solid_tile(self.mouse_pos)
                portal_placement_blocked = cursor_in_noportalzone or cursor_portal_in_noportalzone or cursor_portal_encompassed_by_solid
            else:
                # When paused, use previous values for rendering
                cursor_portal_rect = self.cursor_portal.get_rect()
                cursor_portal_in_noportalzone = False
                cursor_portal_encompassed_by_solid = False
                cursor_over_solid = False
                portal_placement_blocked = False

            if not self.paused:
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
                        # But check for wall collisions first
                        push_amount = abs(player_horizontal_movement) * 2
                        if player_horizontal_movement > 0:  # Player moving right
                            # Check if player is on the left side of spring
                            if player_rect.centerx < spring_rect.centerx:
                                # Test if pushing right would cause a wall collision
                                test_pos_x = spring.pos[0] + push_amount
                                test_rect = pygame.Rect(test_pos_x, spring.pos[1], spring.size[0], spring.size[1])
                                wall_collision = False
                                for rect in self.tilemap.physics_rects_around((test_pos_x, spring.pos[1])):
                                    if test_rect.colliderect(rect):
                                        wall_collision = True
                                        break
                                if not wall_collision:
                                    spring.velocity[0] = push_amount  # Use velocity instead of direct position change
                        elif player_horizontal_movement < 0:  # Player moving left
                            # Check if player is on the right side of spring
                            if player_rect.centerx > spring_rect.centerx:
                                # Test if pushing left would cause a wall collision
                                test_pos_x = spring.pos[0] - push_amount
                                test_rect = pygame.Rect(test_pos_x, spring.pos[1], spring.size[0], spring.size[1])
                                wall_collision = False
                                for rect in self.tilemap.physics_rects_around((test_pos_x, spring.pos[1])):
                                    if test_rect.colliderect(rect):
                                        wall_collision = True
                                        break
                                if not wall_collision:
                                    spring.velocity[0] = -push_amount  # Use velocity instead of direct position change

                # Update spring with physics and collision detection
                entities_to_check = [self.player] + self.crates
                if not spring.teleported_this_frame:
                    spring.update(self.tilemap, entities_to_check)
                    # Check portal teleport for springs
                    if self.check_portal_teleport(spring):
                        spring.teleported_this_frame = True
                else:
                    spring.teleported_this_frame = False
            
            # Check if player fell off the screen
            if not self.dead and not self.transition_active:
                # Player falls off if they go below the display height (with some margin)
                if self.player.pos[1] > self.display.get_height() + 100:
                    self.dead = 1
                    # Play death sound
                    if self.death_sound:
                        self.death_sound.play()

            # Check spike collisions
            if not self.dead and not self.transition_active:
                player_rect = self.player.rect()
                # Check all spike tiles
                for loc in self.tilemap.tilemap:
                    tile = self.tilemap.tilemap[loc]
                    if tile['type'] == 'spikes':
                        tile_x = tile['pos'][0] * self.tilemap.tile_size
                        tile_y = tile['pos'][1] * self.tilemap.tile_size
                        # Get rotation angle (default 0 if not set)
                        rotation = tile.get('rotation', 0)

                        # Calculate spike hitbox based on rotation
                        # Spikes fill full width (16) and half height (8)
                        spike_width = 16  # Full tile width
                        spike_height = 8  # Half tile height
                        if rotation == 0:  # Pointing up (bottom half)
                            spike_rect = pygame.Rect(tile_x, tile_y + 8, spike_width, spike_height)
                        elif rotation == 90:  # Pointing right (left half) - rotated, so full height on left
                            spike_rect = pygame.Rect(tile_x, tile_y, 8, 16)
                        elif rotation == 180:  # Pointing down (top half)
                            spike_rect = pygame.Rect(tile_x, tile_y, spike_width, spike_height)
                        elif rotation == 270:  # Pointing left (right half) - rotated, so full height on right
                            spike_rect = pygame.Rect(tile_x + 8, tile_y, 8, 16)
                        else:
                            # Default to bottom half
                            spike_rect = pygame.Rect(tile_x, tile_y + 8, spike_width, spike_height)

                        if player_rect.colliderect(spike_rect):
                            self.dead = 1
                            # Play death sound
                            if self.death_sound:
                                self.death_sound.play()
                            break

            # Check key collection
            if not self.dead and not self.transition_active and not self.has_key:
                player_rect = self.player.rect()
                key_img = self.assets['key'][0]
                # Get tight bounding rect around non-transparent pixels
                bounding_rect = key_img.get_bounding_rect()
                
                # Check key tiles in tilemap
                for loc in list(self.tilemap.tilemap.keys()):
                    tile = self.tilemap.tilemap[loc]
                    if tile['type'] == 'key':
                        tile_x = tile['pos'][0] * self.tilemap.tile_size
                        tile_y = tile['pos'][1] * self.tilemap.tile_size
                        # Key is 48x48, centered on 16x16 tile
                        # Calculate centered position on tile
                        offset_x = (self.tilemap.tile_size - key_img.get_width()) // 2
                        offset_y = (self.tilemap.tile_size - key_img.get_height()) // 2
                        # Create collision rect using bounding rect
                        key_rect = pygame.Rect(
                            tile_x + offset_x + bounding_rect.x,
                            tile_y + offset_y + bounding_rect.y,
                            bounding_rect.width,
                            bounding_rect.height
                        )
                        if player_rect.colliderect(key_rect):
                            # Collect the key
                            self.has_key = True
                            # Play key sound
                            if self.key_sound:
                                self.key_sound.play()
                            # Remove key from tilemap
                            del self.tilemap.tilemap[loc]
                            break

                # Check key tiles in offgrid_tiles
                if not self.has_key:
                    for tile in self.tilemap.offgrid_tiles[:]:  # Use slice copy to safely remove during iteration
                        if tile['type'] == 'key':
                            # Keys in offgrid_tiles have their pos already centered
                            # Create collision rect using bounding rect
                            key_rect = pygame.Rect(
                                tile['pos'][0] + bounding_rect.x,
                                tile['pos'][1] + bounding_rect.y,
                                bounding_rect.width,
                                bounding_rect.height
                            )
                            if player_rect.colliderect(key_rect):
                                # Collect the key
                                self.has_key = True
                                # Play key sound
                                if self.key_sound:
                                    self.key_sound.play()
                                # Remove key from offgrid_tiles
                                self.tilemap.offgrid_tiles.remove(tile)
                                break

            # Check door collisions
            if not self.dead and not self.transition_active:
                player_rect = self.player.rect()
                # Check if door can be used (no key required OR key collected)
                can_use_door = not self.room_has_key or self.has_key

                if can_use_door:
                    door_img = self.assets['door'][0]
                    # Get tight bounding rect around non-transparent pixels
                    bounding_rect = door_img.get_bounding_rect()
                    
                    # Check door tiles in tilemap
                    for loc in self.tilemap.tilemap:
                        tile = self.tilemap.tilemap[loc]
                        if tile['type'] == 'door':
                            tile_x = tile['pos'][0] * self.tilemap.tile_size
                            tile_y = tile['pos'][1] * self.tilemap.tile_size
                            # Use bounding rect to match image exactly
                            # Center the door on the tile (same as rendering), then apply bounding rect offset
                            offset_x = (self.tilemap.tile_size - door_img.get_width()) // 2
                            offset_y = (self.tilemap.tile_size - door_img.get_height()) // 2
                            door_rect = pygame.Rect(
                                tile_x + offset_x + bounding_rect.x,
                                tile_y + offset_y + bounding_rect.y,
                                bounding_rect.width,
                                bounding_rect.height
                            )
                            if player_rect.colliderect(door_rect):
                                # Trigger win condition
                                self.won = True
                                break

                    # Check door tiles in offgrid_tiles
                    for tile in self.tilemap.offgrid_tiles:
                        if tile['type'] == 'door':
                            # Use bounding rect to match image exactly
                            door_rect = pygame.Rect(
                                tile['pos'][0] + bounding_rect.x,
                                tile['pos'][1] + bounding_rect.y,
                                bounding_rect.width,
                                bounding_rect.height
                            )
                            if player_rect.colliderect(door_rect):
                                # Trigger win condition
                                self.won = True
                                break

            # Check spring_horizontal (horizontal launcher) collisions
            if not self.dead and not self.transition_active:
                player_rect = self.player.rect()
                # Check all spring_horizontal tiles (also handle old red_box tiles for backwards compatibility)
                for loc in self.tilemap.tilemap:
                    tile = self.tilemap.tilemap[loc]
                    if tile['type'] == 'spring_horizontal' or tile['type'] == 'red_box':
                        # Convert old red_box to spring_horizontal
                        if tile['type'] == 'red_box':
                            tile['type'] = 'spring_horizontal'
                        tile_x = tile['pos'][0] * self.tilemap.tile_size
                        tile_y = tile['pos'][1] * self.tilemap.tile_size
                        spring_horizontal_rect = pygame.Rect(tile_x, tile_y, self.tilemap.tile_size, self.tilemap.tile_size)

                        if player_rect.colliderect(spring_horizontal_rect):
                            # Play spring sound
                            if self.spring_sound:
                                self.spring_sound.play()
                            # Determine launch direction based on which side the player is on
                            player_center_x = player_rect.centerx
                            player_center_y = player_rect.centery
                            spring_center_x = spring_horizontal_rect.centerx
                            spring_center_y = spring_horizontal_rect.centery

                            # Calculate horizontal and vertical distances
                            dx = player_center_x - spring_center_x
                            dy = player_center_y - spring_center_y

                            # Launch horizontally based on which side player is on
                            # Use larger horizontal velocity if player is more to the side
                            launch_power = 6.5  # Base launch power
                            if abs(dx) > abs(dy):  # Player is more to the side
                                if dx > 0:  # Player is to the right, launch right
                                    self.player.velocity[0] = launch_power
                                else:  # Player is to the left, launch left
                                    self.player.velocity[0] = -launch_power
                            else:  # Player is more above/below, launch based on horizontal position
                                if dx > 0:  # Player is to the right, launch right
                                    self.player.velocity[0] = launch_power
                                else:  # Player is to the left, launch left
                                    self.player.velocity[0] = -launch_power

            # Camera is static (no player tracking)
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # Render tilemap
            self.tilemap.render(self.display, offset=render_scroll)

            # Render tutorial hints
            for hint in self.tutorial_hints:
                img = self.assets[hint['image']][0]
                self.display.blit(img, (hint['pos'][0] - render_scroll[0], hint['pos'][1] - render_scroll[1]))

            if not self.paused:
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
                        # But first check if the crate would collide with a wall
                        if player_horizontal_movement > 0:  # Player moving right
                            # Check if player is on the left side of crate
                            if player_rect.centerx < crate_rect.centerx:
                                # Check if moving right would cause a wall collision
                                test_pos = crate.pos[0] + abs(player_horizontal_movement) * 2
                                test_rect = pygame.Rect(test_pos, crate.pos[1], crate.size[0], crate.size[1])
                                wall_collision = False
                                for rect in self.tilemap.physics_rects_around((test_pos, crate.pos[1])):
                                    if test_rect.colliderect(rect):
                                        wall_collision = True
                                        break
                                if not wall_collision:
                                    crate.pos[0] += abs(player_horizontal_movement) * 2  # Move crate right
                                else:
                                    crate.velocity[0] = 0  # Stop crate if it would hit a wall
                        elif player_horizontal_movement < 0:  # Player moving left
                            # Check if player is on the right side of crate
                            if player_rect.centerx > crate_rect.centerx:
                                # Check if moving left would cause a wall collision
                                test_pos = crate.pos[0] - abs(player_horizontal_movement) * 2
                                test_rect = pygame.Rect(test_pos, crate.pos[1], crate.size[0], crate.size[1])
                                wall_collision = False
                                for rect in self.tilemap.physics_rects_around((test_pos, crate.pos[1])):
                                    if test_rect.colliderect(rect):
                                        wall_collision = True
                                        break
                                if not wall_collision:
                                    crate.pos[0] -= abs(player_horizontal_movement) * 2  # Move crate left
                                else:
                                    crate.velocity[0] = 0  # Stop crate if it would hit a wall

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

            # Check key collection
            if not self.dead and not self.transition_active:
                player_rect = self.player.rect()
                for key_tile in self.keys[:]:  # Use slice to iterate over copy
                    key_img = self.assets['key'][0]
                    # Get tight bounding rect around non-transparent pixels
                    bounding_rect = key_img.get_bounding_rect()
                    # Create collision rect at the key's position with the bounding rect size
                    key_rect = pygame.Rect(
                        key_tile['pos'][0] + bounding_rect.x,
                        key_tile['pos'][1] + bounding_rect.y,
                        bounding_rect.width,
                        bounding_rect.height
                    )
                    if player_rect.colliderect(key_rect):
                        self.has_key = True
                        # Play key sound
                        if self.key_sound:
                            self.key_sound.play()
                        self.keys.remove(key_tile)
                        # Also remove from tilemap
                        if key_tile in self.tilemap.offgrid_tiles:
                            self.tilemap.offgrid_tiles.remove(key_tile)

            # Check door unlocking
            if not self.dead and not self.transition_active:
                player_rect = self.player.rect()
                for door_tile in self.doors[:]:  # Use slice to iterate over copy
                    door_img = self.assets['door'][0]
                    # Get tight bounding rect around non-transparent pixels
                    bounding_rect = door_img.get_bounding_rect()
                    # Create collision rect at the door's position with the bounding rect size
                    door_rect = pygame.Rect(
                        door_tile['pos'][0] + bounding_rect.x,
                        door_tile['pos'][1] + bounding_rect.y,
                        bounding_rect.width,
                        bounding_rect.height
                    )
                    if player_rect.colliderect(door_rect) and self.has_key:
                        # Unlock door (remove it) and trigger win condition
                        self.doors.remove(door_tile)
                        # Also remove from tilemap
                        if door_tile in self.tilemap.offgrid_tiles:
                            self.tilemap.offgrid_tiles.remove(door_tile)
                        self.has_key = False  # Key is consumed
                        self.won = True  # Trigger win condition

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

            # Render portals - always show both portals (squares around player and cursor)
            self.player_portal.render(self.display, offset=render_scroll)
            # Only render cursor portal if it's not in a noportalzone and not fully encompassed by solid tiles
            if not cursor_portal_in_noportalzone and not cursor_portal_encompassed_by_solid and not cursor_over_solid:
                self.cursor_portal.render(self.display, offset=render_scroll)

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Escape key returns to level selection
                        return "BACK_TO_SELECT"
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_SPACE:
                        if self.player.jump():
                            # Play jump sound effect
                            if self.jump_sound:
                                self.jump_sound.play()
                    if event.key == pygame.K_r:
                        # Restart level
                        self.load_level(self.level)
                    if event.key == pygame.K_p:
                        # Toggle pause
                        self.paused = not self.paused
                    # Enter portal mode when shift is pressed - automatically enters red mode
                    # Only if cursor is not in a blocked zone
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        if not portal_placement_blocked and not self.paused:
                            self.portal_mode = True
                            if self.portal_place_sound:
                                self.portal_place_sound.play()
                            # Automatically lock portals in red mode
                            self.player_portal.lock('left')  # 'left' = red
                            self.cursor_portal.lock('left')
                            self.current_portal_color = 'red'
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    # Exit portal mode when shift is released
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        self.portal_mode = False
                        # Unlock portals when exiting portal mode
                        self.player_portal.unlock()
                        self.cursor_portal.unlock()
                        self.current_portal_color = None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Handle pause menu clicks
                    if self.paused and event.button == 1:  # Left click
                        # Convert screen coordinates to display coordinates
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        display_x = int((mouse_x / self.screen.get_width()) * self.display.get_width())
                        display_y = int((mouse_y / self.screen.get_height()) * self.display.get_height())
                        display_pos = (display_x, display_y)
                        
                        if self.resume_button_rect.collidepoint(display_pos):
                            self.paused = False
                        elif self.quit_button_rect.collidepoint(display_pos):
                            # Return to level selection
                            return "BACK_TO_SELECT"
                    # Only handle portal color cycling if in portal mode (shift held)
                    elif self.portal_mode:
                        # Block portal placement if cursor or cursor portal is over noportalzone
                        if portal_placement_blocked:
                            pass  # Do nothing, portal placement is disabled
                        elif event.button == 1:  # Left click - switch to red portal (only if in white mode)
                            if self.current_portal_color == 'white':
                                self.player_portal.unlock()
                                self.cursor_portal.unlock()
                                self.player_portal.lock('left')  # 'left' = red
                                self.cursor_portal.lock('left')
                                self.current_portal_color = 'red'
                                # Play portal shift sound
                                if self.portal_shift_sound:
                                    self.portal_shift_sound.play()
                        elif event.button == 3:  # Right click - switch to white portal
                            if self.current_portal_color == 'red':
                                self.player_portal.unlock()
                                self.cursor_portal.unlock()
                                self.player_portal.lock('right')  # 'right' = white
                                self.cursor_portal.lock('right')
                                self.current_portal_color = 'white'
                                # Play portal shift sound
                                if self.portal_shift_sound:
                                    self.portal_shift_sound.play()

            # Update transition
            if self.transition_active:
                self.transition_progress += 1.0 / self.transition_duration
                if self.transition_progress >= 1.0:
                    # Transition complete, perform the action
                    self.transition_active = False
                    self.transition_progress = 0

                    if self.transition_type == 'death':
                        self.load_level(self.level)
                        self.dead = 0
                    self.transition_type = None

            # Handle death - start transition if not already active
            if self.dead and not self.transition_active:
                self.transition_active = True
                self.transition_type = 'death'
                self.transition_progress = 0

            # Handle win - show win screen
            win_fade_alpha = 0
            if self.won:
                # Update win screen timer
                self.win_screen_time += dt
                
                # Calculate fade-out: start fading in last 0.3 seconds
                fade_start_time = self.win_screen_duration - 0.3
                if self.win_screen_time >= fade_start_time:
                    fade_progress = min((self.win_screen_time - fade_start_time) / 0.3, 1.0)
                    win_fade_alpha = int(fade_progress * 255)
                
                # Auto-return after win screen duration (and fully faded)
                if self.win_screen_time >= self.win_screen_duration and win_fade_alpha >= 255:
                    return "BACK_TO_SELECT"

            self.display_2.blit(self.display, (0, 0))

            is_level_1 = (isinstance(self.level, int) and self.level == 1) or \
                         (isinstance(self.level, str) and self.level.endswith('level1.json'))

            if not is_level_1:
                # Render control images in top right corner
                control_spacing = 5  # Spacing between control images
                control_y = 5  # Top margin
                
                # Calculate total width of all control images + spacing
                total_width = sum(img.get_width() for img in self.control_images) + (control_spacing * (len(self.control_images) - 1))
                control_start_x = self.display_2.get_width() - total_width - 5  # 5px margin from right edge
                
                # Draw control images from left to right
                current_x = control_start_x
                for img in self.control_images:
                    self.display_2.blit(img, (current_x, control_y))
                    current_x += img.get_width() + control_spacing

            # Render transition overlay (only for death, not win)
            if self.transition_active and self.transition_type != 'win':
                # Calculate fade alpha: fade in to black (0 -> 255) in first half, stay black in second half
                if self.transition_progress < 0.5:
                    # Fade in: 0 to 1 (0% to 50% of transition)
                    fade_alpha = int((self.transition_progress / 0.5) * 255)
                else:
                    # Stay black: 1 (50% to 100% of transition)
                    fade_alpha = 255

                # Create overlay surface
                overlay = pygame.Surface(self.display_2.get_size())
                overlay.fill((0, 0, 0))
                overlay.set_alpha(fade_alpha)
                self.display_2.blit(overlay, (0, 0))

            # Render pause menu overlay
            if self.paused:
                # Semi-transparent dark overlay
                pause_overlay = pygame.Surface(self.display_2.get_size())
                pause_overlay.fill((0, 0, 0))
                pause_overlay.set_alpha(180)
                self.display_2.blit(pause_overlay, (0, 0))
                
                # Draw pause menu buttons
                def draw_pause_button(rect, text):
                    # Draw button background
                    pygame.draw.rect(self.display_2, (50, 50, 50), rect)
                    pygame.draw.rect(self.display_2, (255, 255, 255), rect, 2)
                    # Draw button text
                    button_text = self.pause_font.render(text, False, (255, 255, 255))
                    text_x = rect.centerx - button_text.get_width() // 2
                    text_y = rect.centery - button_text.get_height() // 2
                    self.display_2.blit(button_text, (text_x, text_y))
                
                # Draw "PAUSED" title
                paused_text = self.pause_font.render("PAUSED", False, (255, 255, 255))
                paused_x = self.display_2.get_width() // 2 - paused_text.get_width() // 2
                paused_y = self.resume_button_rect.y - 40
                self.display_2.blit(paused_text, (paused_x, paused_y))
                
                # Scale button rects to display_2 coordinates
                resume_rect = pygame.Rect(
                    int(self.resume_button_rect.x * (self.display_2.get_width() / self.display.get_width())),
                    int(self.resume_button_rect.y * (self.display_2.get_height() / self.display.get_height())),
                    int(self.resume_button_rect.width * (self.display_2.get_width() / self.display.get_width())),
                    int(self.resume_button_rect.height * (self.display_2.get_height() / self.display.get_height()))
                )
                quit_rect = pygame.Rect(
                    int(self.quit_button_rect.x * (self.display_2.get_width() / self.display.get_width())),
                    int(self.quit_button_rect.y * (self.display_2.get_height() / self.display.get_height())),
                    int(self.quit_button_rect.width * (self.display_2.get_width() / self.display.get_width())),
                    int(self.quit_button_rect.height * (self.display_2.get_height() / self.display.get_height()))
                )
                
                draw_pause_button(resume_rect, "RESUME")
                draw_pause_button(quit_rect, "QUIT")

            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), (0, 0))
            
            # Render win screen overlay
            if self.won:
                # Load winning background image
                game_dir = os.path.dirname(os.path.abspath(__file__))
                winning_bg_path = os.path.join(game_dir, 'data', 'homepage-assets', 'winning_bg.png')
                try:
                    winning_bg = pygame.image.load(winning_bg_path).convert()
                    winning_bg = pygame.transform.scale(winning_bg, self.screen.get_size())
                    # Draw winning background to cover the screen
                    self.screen.blit(winning_bg, (0, 0))
                except:
                    # Fallback if image not found - show semi-transparent overlay
                    overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))
                    self.screen.blit(overlay, (0, 0))
                
                # Load fonts for text
                font_path = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
                try:
                    title_font = pygame.font.Font(font_path, 32)  # Increased from 24 to 32
                    message_font = pygame.font.Font(font_path, 16)  # Increased from 8 to 16 (doubled)
                except:
                    title_font = pygame.font.Font(None, 64)
                    message_font = pygame.font.Font(None, 48)
                
                # Helper function to render outlined text
                def render_outlined(text, font, fg, outline, thickness=2):
                    base = font.render(text, False, fg).convert_alpha()
                    w, h = base.get_size()
                    surf = pygame.Surface((w + thickness * 2, h + thickness * 2), pygame.SRCALPHA)
                    # Outline
                    for ox in range(-thickness, thickness + 1):
                        for oy in range(-thickness, thickness + 1):
                            if ox * ox + oy * oy <= thickness * thickness:
                                if ox != 0 or oy != 0:
                                    s = font.render(text, False, outline).convert_alpha()
                                    surf.blit(s, (ox + thickness, oy + thickness))
                    surf.blit(base, (thickness, thickness))
                    return surf
                
                # Render both texts with outline to get their sizes
                title_text = "The Goat Prevails!"
                title_color = (255, 215, 0)  # Gold color for winning
                title_outline = (0, 0, 0)  # Black outline
                title_surf = render_outlined(title_text, title_font, title_color, title_outline, thickness=3)
                
                # Split message into multiple lines to fit on page
                message_line1 = "You have completed the level!"
                message_line2 = ""
                message_color = (255, 215, 0)  # Gold color for winning
                message_outline = (0, 0, 0)  # Black outline
                message_surf1 = render_outlined(message_line1, message_font, message_color, message_outline, thickness=2)
                message_surf2 = render_outlined(message_line2, message_font, message_color, message_outline, thickness=2)
                
                # Calculate combined message height
                line_spacing = 10
                message_total_width = max(message_surf1.get_width(), message_surf2.get_width())
                message_total_height = message_surf1.get_height() + message_surf2.get_height() + line_spacing
                
                # Calculate rectangle dimensions to fit both title and message with bigger padding
                padding = 50  # Increased padding for bigger rectangle
                spacing = 30  # Space between title and message
                rect_width = max(title_surf.get_width(), message_total_width) + (padding * 2)
                rect_height = title_surf.get_height() + message_total_height + spacing + (padding * 2)
                rect_x = (self.screen.get_width() - rect_width) // 2
                rect_y = (self.screen.get_height() - rect_height) // 2
                
                # Draw semi-transparent light gray rounded rectangle
                rect_surf = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
                gray_color = (220, 220, 220)  # Light gray
                pygame.draw.rect(rect_surf, gray_color, (0, 0, rect_width, rect_height), border_radius=15)
                rect_surf.set_alpha(220)  # Slightly opaque (about 86% opacity)
                self.screen.blit(rect_surf, (rect_x, rect_y))
                
                # Calculate vertical positions inside the rectangle
                content_start_y = rect_y + padding
                title_y = content_start_y
                message_start_y = title_y + title_surf.get_height() - 6 + spacing  # Adjust for outline offset
                
                # Render title centered in the rectangle
                title_x = rect_x + (rect_width - title_surf.get_width()) // 2
                self.screen.blit(title_surf, (title_x, title_y))
                
                # Render message lines centered in the rectangle
                message_line1_x = rect_x + (rect_width - message_surf1.get_width()) // 2
                message_line1_y = message_start_y
                self.screen.blit(message_surf1, (message_line1_x, message_line1_y))
                
                message_line2_x = rect_x + (rect_width - message_surf2.get_width()) // 2
                message_line2_y = message_line1_y + message_surf1.get_height() + line_spacing
                self.screen.blit(message_surf2, (message_line2_x, message_line2_y))
                
                # Apply fade-out overlay if fading
                if win_fade_alpha > 0:
                    fade_overlay = pygame.Surface(self.screen.get_size())
                    fade_overlay.fill((0, 0, 0))
                    fade_overlay.set_alpha(win_fade_alpha)
                    self.screen.blit(fade_overlay, (0, 0))
            
            # Render custom cursor at mouse position (centered)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            cursor_x = mouse_x - self.cursor_img.get_width() // 2
            cursor_y = mouse_y - self.cursor_img.get_height() // 2
            self.screen.blit(self.cursor_img, (cursor_x, cursor_y))
            
            pygame.display.update()


if __name__ == "__main__":
    Game().run()
