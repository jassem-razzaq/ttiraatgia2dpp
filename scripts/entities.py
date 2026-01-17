import math
import pygame

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        if hasattr(game, 'assets') and e_type + '/idle' in game.assets:
            self.set_action('idle')
        
        self.last_movement = [0, 0]
        self.last_pos = list(pos)
        self.teleported_this_frame = False
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action and hasattr(self.game, 'assets'):
            if self.type + '/' + action in self.game.assets:
                self.action = action
                self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0), additional_colliders=None):
        self.last_pos = self.pos.copy()
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        # Check collisions with additional colliders (like crates) for horizontal movement
        # Crates don't block horizontal movement - player passes through sides
        if additional_colliders:
            entity_rect = self.rect()
            for collider in additional_colliders:
                if collider == self:  # Don't collide with self
                    continue
                # Skip horizontal collision with crates - player can pass through sides
                if hasattr(self, 'type') and self.type == 'player' and hasattr(collider, 'type') and collider.type == 'crate':
                    continue
                collider_rect = collider.rect()
                if entity_rect.colliderect(collider_rect):
                    # Normal collision handling for non-crates
                    if frame_movement[0] > 0:
                        entity_rect.right = collider_rect.left
                        self.collisions['right'] = True
                    if frame_movement[0] < 0:
                        entity_rect.left = collider_rect.right
                        self.collisions['left'] = True
                    self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
        
        # Check collisions with additional colliders (like crates) for vertical movement
        if additional_colliders:
            entity_rect = self.rect()
            for collider in additional_colliders:
                if collider == self:  # Don't collide with self
                    continue
                collider_rect = collider.rect()
                if entity_rect.colliderect(collider_rect):
                    # For crates, only check top edge collision (when player is landing from above)
                    if hasattr(self, 'type') and self.type == 'player' and hasattr(collider, 'type') and collider.type == 'crate':
                        # Only handle top edge - player landing on crate (moving down)
                        if frame_movement[1] > 0:  # Player moving down
                            # Check if player is above the crate (player's bottom should be at crate's top)
                            if entity_rect.bottom <= collider_rect.top + 5:  # Small tolerance for landing
                                entity_rect.bottom = collider_rect.top
                                self.collisions['down'] = True
                                self.pos[1] = entity_rect.y
                        # Don't handle bottom collision (player can pass through bottom)
                    else:
                        # Normal collision handling for non-crates
                        if frame_movement[1] > 0:
                            entity_rect.bottom = collider_rect.top
                            self.collisions['down'] = True
                        if frame_movement[1] < 0:
                            entity_rect.top = collider_rect.bottom
                            self.collisions['up'] = True
                        self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        self.velocity[1] = min(10, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        if hasattr(self, 'animation'):
            self.animation.update()
    
    def render(self, surf, offset=(0, 0)):
        if hasattr(self, 'animation'):
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), 
                     (self.pos[0] - offset[0] + self.anim_offset[0], 
                      self.pos[1] - offset[1] + self.anim_offset[1]))
        else:
            # Fallback rendering
            pygame.draw.rect(surf, (255, 0, 0), 
                           (self.pos[0] - offset[0], self.pos[1] - offset[1], 
                            self.size[0], self.size[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
    
    def update(self, tilemap, movement=(0, 0), additional_colliders=None):
        super().update(tilemap, movement=movement, additional_colliders=additional_colliders)
        
        self.air_time += 1
        
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
            
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
                
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
                
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
        return False

class Crate(PhysicsEntity):
    def __init__(self, game, pos, size=(16, 16)):
        # Use the actual box image size for the collision box if available
        if hasattr(game, 'assets') and 'box' in game.assets:
            box_img = game.assets['box']
            # Use the actual image dimensions for the collision box
            size = (box_img.get_width(), box_img.get_height())
        super().__init__(game, 'crate', pos, size)
        self.being_pushed = False
        
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        
        # Crates have friction (gravity is handled by PhysicsEntity parent class)
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.15, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.15, 0)
    
    def render(self, surf, offset=(0, 0)):
        # Render box image if available
        if hasattr(self.game, 'assets') and 'box' in self.game.assets:
            box_img = self.game.assets['box']
            surf.blit(box_img, (self.pos[0] - offset[0], self.pos[1] - offset[1]))
        else:
            # Fallback: Draw brown crate
            pygame.draw.rect(surf, (139, 69, 19), 
                            (self.pos[0] - offset[0], self.pos[1] - offset[1], 
                             self.size[0], self.size[1]))
            pygame.draw.rect(surf, (101, 50, 14), 
                            (self.pos[0] - offset[0], self.pos[1] - offset[1], 
                             self.size[0], self.size[1]), 2)
