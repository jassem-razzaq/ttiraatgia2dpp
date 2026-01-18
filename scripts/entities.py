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
        
        # If crate collided with a wall horizontally, stop horizontal movement immediately
        if self.collisions['left'] or self.collisions['right']:
            self.velocity[0] = 0
        
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

class Spring:
    def __init__(self, game, pos):
        """
        Bottom-attached spring entity that can be pushed left/right and launches entities upward.
        
        Args:
            game: Game instance
            pos: Position tuple (x, y)
        """
        self.game = game
        self.pos = list(pos)
        self.velocity = [0, 0]  # For physics-based pushing
        
        # Load spring image as-is without scaling, with alpha transparency
        import os
        game_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spring_path = os.path.join(game_dir, 'data', 'images', 'spring.png')
        spring_img = pygame.image.load(spring_path).convert_alpha()  # Preserve alpha channel
        # Use original image size
        self.base_image = spring_img
        self.image = self.base_image.copy()
        
        # Size for collision detection - use actual image size
        self.size = (spring_img.get_width(), spring_img.get_height())
        
        # No animation state - removed animations
        
        # Collision state - track which entities are currently touching and when they were launched
        self.touching_entities = set()  # Entities currently touching the spring
        self.launched_entities = {}  # Track when each entity was last launched {entity_id: frame_count}
        self.bounced_entities = set()  # Track which entities have been bounced (reset when they hit ground)
        
        # Cooldown state - spring is inactive for 5 seconds after use
        self.cooldown_timer = 0  # Frames remaining in cooldown (300 frames = 5 seconds at 60fps)
        self.is_active = True  # Whether spring can bounce entities
        
        # NEW: Track the current bounce height for each entity to maintain constant bounces
        self.entity_bounce_heights = {}  # {entity_id: launch_power}
        
        # Constants for bounce behavior
        self.BASE_BOUNCE_POWER = 3.0  # Base constant bounce height (normal bounce)
        self.MIN_HIGH_JUMP_VELOCITY = 5.0  # Minimum impact velocity to trigger high bounce
        self.HIGH_BOUNCE_MULTIPLIER = 0.6  # Multiplier for high jumps (reduced from 0.8)
        self.MAX_BOUNCE_POWER = 6.0  # Absolute maximum launch power
        
        # For portal teleport tracking
        self.last_pos = list(pos)
        self.teleported_this_frame = False
        
    def rect(self):
        """Get collision rect for the spring"""
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def update(self, tilemap, entities):
        """
        Update spring physics (pushing, gravity), animation, and check for collisions with entities.
        
        Args:
            tilemap: Tilemap instance for physics
            entities: List of entities to check collisions with (like player, crates)
        """
        self.last_pos = self.pos.copy()
        
        # Cooldown removed - spring is always active
        self.is_active = True
        
        # Apply gravity (like other entities)
        self.velocity[1] = min(10, self.velocity[1] + 0.1)
        
        # Apply physics (friction for horizontal movement)
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
        
        # Move spring horizontally
        self.pos[0] += self.velocity[0]
        
        # Check horizontal collisions with tilemap
        spring_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if spring_rect.colliderect(rect):
                # Only handle horizontal collision if we're moving horizontally
                if self.velocity[0] > 0:
                    spring_rect.right = rect.left
                    self.pos[0] = spring_rect.x
                    self.velocity[0] = 0
                elif self.velocity[0] < 0:
                    spring_rect.left = rect.right
                    self.pos[0] = spring_rect.x
                    self.velocity[0] = 0
        
        # Move spring vertically
        self.pos[1] += self.velocity[1]
        
        # Check vertical collisions with tilemap
        spring_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if spring_rect.colliderect(rect):
                # Only handle vertical collision based on vertical movement
                if self.velocity[1] > 0:  # Falling
                    spring_rect.bottom = rect.top
                    self.pos[1] = spring_rect.y
                    self.velocity[1] = 0
                elif self.velocity[1] < 0:  # Moving up
                    spring_rect.top = rect.bottom
                    self.pos[1] = spring_rect.y
                    self.velocity[1] = 0
                # If velocity is 0, don't adjust position (spring is resting)
        
        spring_rect = self.rect()
        
        # Reset bounce tracking for entities that have hit the ground (not just the spring)
        for entity in entities:
            if hasattr(entity, 'collisions') and hasattr(entity, 'rect'):
                entity_id = id(entity)
                # If entity is on the ground (tilemap collision, not spring), they can be bounced again
                # Check that they're actually on a solid surface, not just touching the spring
                if entity.collisions.get('down', False):
                    # Make sure they're not just touching the spring - check if they're on a tile
                    entity_rect = entity.rect()
                    on_tile = False
                    for rect in tilemap.physics_rects_around(entity.pos):
                        if entity_rect.bottom <= rect.top + 2 and entity_rect.bottom >= rect.top - 2:
                            on_tile = True
                            break
                    # Only reset if they're on actual ground, not just the spring
                    if on_tile:
                        self.bounced_entities.discard(entity_id)
                        # Reset the stored bounce height when entity touches ground
                        if entity_id in self.entity_bounce_heights:
                            del self.entity_bounce_heights[entity_id]
        
        # Track which entities are currently touching
        currently_touching = set()
        
        # Check collisions with entities
        for entity in entities:
            if not hasattr(entity, 'rect'):
                continue
            entity_rect = entity.rect()
            entity_id = id(entity)  # Unique ID for each entity
            
            # Check current collision
            is_colliding = spring_rect.colliderect(entity_rect)
            
            # Also check if entity passed through spring (for fast-moving entities)
            # Check if entity's previous position and current position create a line that intersects spring
            if not is_colliding and hasattr(entity, 'last_pos'):
                # Create a larger detection area above the spring for fast-falling entities
                detection_rect = pygame.Rect(spring_rect.x - 2, spring_rect.y - 8, spring_rect.width + 4, spring_rect.height + 8)
                if detection_rect.colliderect(entity_rect):
                    # Check if entity is moving down and would have passed through spring
                    if hasattr(entity, 'velocity') and entity.velocity[1] > 0:
                        # Entity is falling and in detection area - treat as collision
                        is_colliding = True
            
            if is_colliding:
                currently_touching.add(entity_id)
                
                # Only launch if:
                # - Entity just started touching from above (wasn't touching last frame)
                # - Entity is landing on spring (moving downward)
                # Check if entity is landing on spring (entity bottom touching spring top)
                if entity_id not in self.touching_entities and entity.velocity[1] >= 0:
                    if hasattr(entity, 'velocity'):
                        # Check if entity is landing on top of spring (moving down)
                        # More lenient check for fast-moving entities
                        if entity_rect.bottom <= spring_rect.top + 6:
                            # Calculate impact velocity - only use downward motion
                            # Velocity[1] is positive when falling (downward in pygame)
                            # Only count downward velocity (ignore upward velocity)
                            velocity_based = max(0, entity.velocity[1])  # Positive = downward, ignore negative
                            
                            # Also check position change for fast entities that might have passed through
                            position_based = 0
                            if hasattr(entity, 'last_pos'):
                                # Calculate actual distance fallen this frame (only if moving down)
                                distance_fallen = entity.pos[1] - entity.last_pos[1]
                                position_based = max(0, distance_fallen)  # Only positive (downward) movement
                            
                            # Use the larger value to catch fast-moving entities
                            impact_velocity = max(velocity_based, position_based)
                            
                            # Determine launch power based on impact velocity:
                            # - Higher impact velocity (falling from higher) = higher bounce
                            # - Base bounce power + velocity multiplier
                            
                            if impact_velocity >= self.MIN_HIGH_JUMP_VELOCITY:
                                # High impact - calculate proportional bounce
                                launch_power = self.BASE_BOUNCE_POWER + impact_velocity * self.HIGH_BOUNCE_MULTIPLIER
                                launch_power = min(launch_power, self.MAX_BOUNCE_POWER)
                            else:
                                # Normal bounce - use base power
                                launch_power = self.BASE_BOUNCE_POWER
                            
                            # Launch entity UP - REPLACE velocity (don't add to existing upward velocity)
                            entity.velocity[1] = -launch_power
                            
                            # Play spring sound if entity is player
                            if hasattr(entity, 'type') and entity.type == 'player':
                                if hasattr(self.game, 'spring_sound') and self.game.spring_sound:
                                    self.game.spring_sound.play()
                            
                            # No animation - removed
                            self.launched_entities[entity_id] = 0
        
        # Update touching entities for next frame
        self.touching_entities = currently_touching
        
        # No animation update - removed animations
    
    def render(self, surf, offset=(0, 0)):
        """Render the spring without any animation or effects"""
        spring_img = self.base_image.copy()
        
        # Render at position without any scaling or animation
        render_x = self.pos[0] - offset[0]
        render_y = self.pos[1] - offset[1]
        
        surf.blit(spring_img, (render_x, render_y))
