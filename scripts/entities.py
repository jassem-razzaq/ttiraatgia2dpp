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
        
        # Load and scale spring image (half player size - player is 8x15, so spring ~4x8)
        from scripts.utils import load_image
        spring_img = load_image('spring.png', colorkey=(255, 255, 255))  # White colorkey
        # Scale to approximately half player size
        self.base_image = pygame.transform.scale(spring_img, (4, 8))
        self.image = self.base_image.copy()
        
        # Size for collision detection - make hitbox larger to catch fast-moving entities
        # Visual size is 4x8, but collision box is larger (8x12) to prevent fast entities from passing through
        self.size = (8, 12)  # Wider and taller collision box
        
        # Animation state
        self.animation_frame = 0  # 0 = normal, >0 = animating
        self.animation_timer = 0
        self.scale = 1.0  # Current scale for animation
        
        # Collision state - track which entities are currently touching and when they were launched
        self.touching_entities = set()  # Entities currently touching the spring
        self.launched_entities = {}  # Track when each entity was last launched {entity_id: frame_count}
        self.bounced_entities = set()  # Track which entities have been bounced (reset when they hit ground)
        
        # Cooldown state - spring is inactive for 5 seconds after use
        self.cooldown_timer = 0  # Frames remaining in cooldown (300 frames = 5 seconds at 60fps)
        self.is_active = True  # Whether spring can bounce entities
        
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
        
        # Update cooldown timer
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
            self.is_active = False  # Spring is inactive during cooldown
        else:
            self.is_active = True  # Spring is active and can bounce
        
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
                if self.velocity[0] > 0:
                    spring_rect.right = rect.left
                if self.velocity[0] < 0:
                    spring_rect.left = rect.right
                self.pos[0] = spring_rect.x
                self.velocity[0] = 0
        
        # Move spring vertically
        self.pos[1] += self.velocity[1]
        
        # Check vertical collisions with tilemap
        spring_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if spring_rect.colliderect(rect):
                if self.velocity[1] > 0:  # Falling
                    spring_rect.bottom = rect.top
                    self.velocity[1] = 0
                if self.velocity[1] < 0:  # Moving up
                    spring_rect.top = rect.bottom
                    self.velocity[1] = 0
                self.pos[1] = spring_rect.y
        
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
                # - Entity hasn't been bounced yet (until they hit ground)
                # - Spring is active (not in cooldown)
                # Check if entity is landing on spring (entity bottom touching spring top)
                if entity_id not in self.touching_entities and entity_id not in self.bounced_entities and self.is_active:
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
                            
                            # Base launch power + impact velocity multiplier
                            # Launch power proportional to impact velocity
                            # Reduced multiplier to prevent excessive height gain
                            launch_power = 1.5 + impact_velocity * 0.8
                            # Cap maximum launch power more strictly to prevent infinite height
                            launch_power = min(launch_power, 6.0)
                            
                            # Launch entity UP - REPLACE velocity (don't add to existing upward velocity)
                            # If entity is already moving up, use the larger of current upward velocity or launch power
                            # This prevents stacking but allows higher bounces from faster falls
                            if entity.velocity[1] < 0:  # Already moving up
                                # Use the larger upward velocity (more negative = higher)
                                entity.velocity[1] = min(entity.velocity[1], -launch_power)
                            else:  # Moving down or stationary
                                # Set to launch power
                                entity.velocity[1] = -launch_power
                            
                            # Mark entity as bounced - they can't be bounced again until they hit ground
                            self.bounced_entities.add(entity_id)
                            
                            # Start cooldown - spring is inactive for 5 seconds (300 frames at 60fps)
                            self.cooldown_timer = 300
                            self.is_active = False
                            
                            # Start animation
                            self.animation_timer = 0
                            self.animation_frame = 0
                            self.launched_entities[entity_id] = self.animation_timer
        
        # Update touching entities for next frame
        self.touching_entities = currently_touching
        
        # Update animation
        if self.animation_timer >= 0:
            self.animation_timer += 1
            
            # Animation: shrink (0-10 frames), then expand (10-20 frames)
            if self.animation_timer < 10:
                # Shrinking phase
                self.scale = 1.0 - (self.animation_timer / 10.0) * 0.5  # Shrink to 50%
            elif self.animation_timer < 20:
                # Expanding phase
                progress = (self.animation_timer - 10) / 10.0
                self.scale = 0.5 + progress * 0.5  # Expand back to 100%
            else:
                # Animation complete
                self.scale = 1.0
                self.animation_timer = -1
    
    def render(self, surf, offset=(0, 0)):
        """Render the spring with current animation scale (no rotation, just scaled)"""
        spring_img = self.base_image.copy()
        
        # Scale based on animation
        if self.scale != 1.0:
            new_size = (int(spring_img.get_width() * self.scale), int(spring_img.get_height() * self.scale))
            if new_size[0] > 0 and new_size[1] > 0:
                spring_img = pygame.transform.scale(spring_img, new_size)
        
        # Calculate position to center scaled image
        render_x = self.pos[0] - offset[0] + (self.size[0] - spring_img.get_width()) // 2
        render_y = self.pos[1] - offset[1] + (self.size[1] - spring_img.get_height()) // 2
        
        surf.blit(spring_img, (render_x, render_y))
