import pygame
import math

class Portal:
    def __init__(self, game, size=64):
        self.game = game
        self.size = size
        self.pos = [0, 0]
        self.locked = False
        self.lock_type = None  # 'left' for opposite edge (red), 'right' for adjacent edge (white)
        self.locked_pos = [0, 0]
        self.color = (200, 200, 200)  # Default gray
        self.thickness = 2
        
        # Portal animations
        if hasattr(game, 'assets'):
            self.red_animation = game.assets.get('portal/red', None)
            self.white_animation = game.assets.get('portal/white', None)
            if self.red_animation:
                self.red_animation = self.red_animation.copy()
            if self.white_animation:
                self.white_animation = self.white_animation.copy()
        else:
            self.red_animation = None
            self.white_animation = None
        
    def update(self, follow_pos):
        if not self.locked:
            # Center the portal on the follow position
            self.pos[0] = follow_pos[0] - self.size // 2
            self.pos[1] = follow_pos[1] - self.size // 2
        else:
            # Keep locked position
            self.pos = self.locked_pos.copy()
        
        # Update animations
        if self.red_animation:
            self.red_animation.update()
        if self.white_animation:
            self.white_animation.update()
    
    def lock(self, lock_type):
        self.locked = True
        self.lock_type = lock_type
        self.locked_pos = self.pos.copy()
        
        if lock_type == 'left':
            self.color = (100, 150, 255)  # Bright red
            self.thickness = 4
        elif lock_type == 'right':
            self.color = (255, 150, 50)  # Bright white
            self.thickness = 4
    
    def unlock(self):
        self.locked = False
        self.lock_type = None
        self.color = (200, 200, 200)  # Gray
        self.thickness = 2
    
    def get_rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size, self.size)
    
    def is_inside(self, rect):
        """Check if a rectangle is inside the portal (overlaps significantly)"""
        portal_rect = self.get_rect()
        # Check if the entity's center is inside the portal
        center_x = rect.centerx
        center_y = rect.centery
        return (center_x >= portal_rect.left and 
                center_x <= portal_rect.right and
                center_y >= portal_rect.top and
                center_y <= portal_rect.bottom)
    
    def check_collision(self, entity_rect, last_rect):
        """
        Check if entity is exiting the portal (going from inside to outside).
        Returns a tuple (edge, relative_position) or None.
        
        relative_position is a value between 0 and 1 representing where along the edge
        the entity crossed (0 = start of edge, 1 = end of edge).
        
        How it works:
        - We check if the entity was inside the portal in the last frame
        - And if it's now crossing an edge to exit
        - We determine which edge it's crossing based on position
        - We calculate the relative position along that edge
        """
        portal_rect = self.get_rect()
        
        # Check if entity was inside the portal last frame (center was inside)
        was_inside = self.is_inside(last_rect)
        
        # Only trigger if entity was inside
        if not was_inside:
            return None
        
        # Check if entity is now crossing an edge to exit
        # Use a threshold to determine edge crossing
        threshold = 8
        
        # Check if crossing left edge (entity's right side is past portal's left edge)
        if last_rect.right > portal_rect.left and entity_rect.right <= portal_rect.left + threshold:
            # Calculate relative position along the left edge (vertical edge)
            # Use the entity's center Y position relative to the portal's top
            entity_center_y = last_rect.centery
            relative_pos = (entity_center_y - portal_rect.top) / portal_rect.height
            relative_pos = max(0, min(1, relative_pos))  # Clamp between 0 and 1
            return ('left', relative_pos)
        # Check if crossing right edge (entity's left side is past portal's right edge)
        elif last_rect.left < portal_rect.right and entity_rect.left >= portal_rect.right - threshold:
            # Calculate relative position along the right edge (vertical edge)
            entity_center_y = last_rect.centery
            relative_pos = (entity_center_y - portal_rect.top) / portal_rect.height
            relative_pos = max(0, min(1, relative_pos))  # Clamp between 0 and 1
            return ('right', relative_pos)
        # Check if crossing top edge (entity's bottom is past portal's top edge)
        elif last_rect.bottom > portal_rect.top and entity_rect.bottom <= portal_rect.top + threshold:
            # Calculate relative position along the top edge (horizontal edge)
            # Use the entity's center X position relative to the portal's left
            entity_center_x = last_rect.centerx
            relative_pos = (entity_center_x - portal_rect.left) / portal_rect.width
            relative_pos = max(0, min(1, relative_pos))  # Clamp between 0 and 1
            return ('top', relative_pos)
        # Check if crossing bottom edge (entity's top is past portal's bottom edge)
        elif last_rect.top < portal_rect.bottom and entity_rect.top >= portal_rect.bottom - threshold:
            # Calculate relative position along the bottom edge (horizontal edge)
            entity_center_x = last_rect.centerx
            relative_pos = (entity_center_x - portal_rect.left) / portal_rect.width
            relative_pos = max(0, min(1, relative_pos))  # Clamp between 0 and 1
            return ('bottom', relative_pos)
        
        return None
    
    def teleport_entity(self, entity, exit_portal, exit_edge, relative_position):
        """
        Teleport entity through portal and preserve/transform momentum.
        
        exit_edge: The edge of THIS portal that the entity is exiting from
        exit_portal: The portal the entity will appear in
        relative_position: A value between 0 and 1 representing where along the exit_edge
                          the entity crossed (0 = start of edge, 1 = end of edge)
        
        Entities appear INSIDE the exit portal, near the entry edge, so they can
        then exit from the opposite/adjacent edge.
        
        Momentum is preserved and transformed based on the edge transformation:
        - red portals: Opposite direction (reverse velocity)
        - white portals: Perpendicular direction (rotate velocity 90 degrees clockwise)
        
        For red portals (left click):
        - Exit from right edge → Enter from left edge (inside, near left edge)
        - Exit from left edge → Enter from right edge (inside, near right edge)
        - Exit from top edge → Enter from bottom edge (inside, near bottom edge)
        - Exit from bottom edge → Enter from top edge (inside, near top edge)
        
        For white portals (right click):
        - Exit from right edge → Enter from bottom edge (inside, near bottom edge)
        - Exit from bottom edge → Enter from right edge (inside, near right edge)
        - Exit from left edge → Enter from top edge (inside, near top edge)
        - Exit from top edge → Enter from left edge (inside, near left edge) - launches rightward
        """
        if not self.locked or not exit_portal.locked:
            return False
        
        # Capture velocity before teleportation
        old_velocity = entity.velocity.copy()
        
        exit_rect = exit_portal.get_rect()
        
        # Small offset to place entity just inside the portal (not at the exact edge)
        offset = 4
        
        if self.lock_type == 'left':  # red portal - opposite edge
            # Exit from one edge, enter from opposite edge going inside
            # Momentum is preserved in the same direction as entry
            if exit_edge == 'left':  # Exiting left edge, enter from right edge (inside, near right)
                entity.pos[0] = exit_rect.right - entity.size[0] - offset
                # Use relative_position to place entity at same position along the vertical edge
                entity.pos[1] = exit_rect.top + (relative_position * exit_rect.height) - entity.size[1] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[1] = max(exit_rect.top, min(exit_rect.bottom - entity.size[1], entity.pos[1]))
                # Entering from right (moving left), exit going left (preserve leftward motion)
                # If was moving left (negative), keep moving left
                entity.velocity[0] = old_velocity[0] if old_velocity[0] < 0 else -abs(old_velocity[0])
                entity.velocity[1] = old_velocity[1]  # Keep vertical velocity
            elif exit_edge == 'right':  # Exiting right edge, enter from left edge (inside, near left)
                entity.pos[0] = exit_rect.left + offset
                # Use relative_position to place entity at same position along the vertical edge
                entity.pos[1] = exit_rect.top + (relative_position * exit_rect.height) - entity.size[1] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[1] = max(exit_rect.top, min(exit_rect.bottom - entity.size[1], entity.pos[1]))
                # Entering from left (moving right), exit going right (preserve rightward motion)
                # If was moving right (positive), keep moving right
                entity.velocity[0] = old_velocity[0] if old_velocity[0] > 0 else abs(old_velocity[0])
                entity.velocity[1] = old_velocity[1]  # Keep vertical velocity
            elif exit_edge == 'top':  # Exiting top edge, enter from bottom edge (inside, near bottom)
                # Use relative_position to place entity at same position along the horizontal edge
                entity.pos[0] = exit_rect.left + (relative_position * exit_rect.width) - entity.size[0] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[0] = max(exit_rect.left, min(exit_rect.right - entity.size[0], entity.pos[0]))
                entity.pos[1] = exit_rect.bottom - entity.size[1] - offset
                # Entering from bottom (moving up), exit going up (preserve upward motion)
                # If was moving up (negative), keep moving up
                entity.velocity[0] = old_velocity[0]  # Keep horizontal velocity
                entity.velocity[1] = old_velocity[1] if old_velocity[1] < 0 else -abs(old_velocity[1])
            elif exit_edge == 'bottom':  # Exiting bottom edge, enter from top edge (inside, near top)
                # Use relative_position to place entity at same position along the horizontal edge
                entity.pos[0] = exit_rect.left + (relative_position * exit_rect.width) - entity.size[0] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[0] = max(exit_rect.left, min(exit_rect.right - entity.size[0], entity.pos[0]))
                entity.pos[1] = exit_rect.top + offset
                # Entering from top (moving down), exit going down (preserve downward motion)
                # If was moving down (positive), keep moving down
                entity.velocity[0] = old_velocity[0]  # Keep horizontal velocity
                entity.velocity[1] = old_velocity[1] if old_velocity[1] > 0 else abs(old_velocity[1])
                
        elif self.lock_type == 'right':  # white portal - adjacent edge (counter-clockwise exit rotation)
            # Enter right → Exit bottom (moving right → moving down)
            # Enter bottom → Exit right (moving down → moving left)
            # Enter left → Exit top (moving left → moving up)
            # Enter top → Exit left (moving up → moving right)
            if exit_edge == 'right':  # Exiting right edge, enter from bottom edge (inside, near bottom)
                # Use relative_position to place entity at same position along the horizontal edge
                entity.pos[0] = exit_rect.left + (relative_position * exit_rect.width) - entity.size[0] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[0] = max(exit_rect.left, min(exit_rect.right - entity.size[0], entity.pos[0]))
                entity.pos[1] = exit_rect.bottom - entity.size[1] - offset
                # Entering from right (moving right), exit going UP from bottom edge
                # Take horizontal velocity magnitude, convert to vertical UP velocity (preserve momentum)
                # Use the magnitude of horizontal velocity (whether left or right) to determine launch speed
                horizontal_speed = abs(old_velocity[0])
                # If no horizontal velocity, use a minimum launch speed based on vertical velocity or default
                if horizontal_speed == 0:
                    horizontal_speed = abs(old_velocity[1]) if abs(old_velocity[1]) > 0 else 2.0  # Fallback to vertical or minimum
                entity.velocity[0] = 0
                entity.velocity[1] = -horizontal_speed  # Upward (negative Y) - launch upward with conserved momentum
            elif exit_edge == 'bottom':  # Exiting bottom edge, enter from RIGHT edge (inside, near right)
                entity.pos[0] = exit_rect.right - entity.size[0] - offset
                # Use relative_position to place entity at same position along the vertical edge
                entity.pos[1] = exit_rect.top + (relative_position * exit_rect.height) - entity.size[1] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[1] = max(exit_rect.top, min(exit_rect.bottom - entity.size[1], entity.pos[1]))
                # Entering from bottom (moving down), exit going left from right edge
                # Take vertical down velocity, convert to horizontal left velocity
                speed = abs(old_velocity[1]) if old_velocity[1] > 0 else 0
                entity.velocity[0] = -speed  # Leftward (negative X)
                entity.velocity[1] = 0
            elif exit_edge == 'left':  # Exiting left edge (entering from left), exit from top edge going downward
                # Use relative_position to place entity at same position along the horizontal edge
                entity.pos[0] = exit_rect.left + (relative_position * exit_rect.width) - entity.size[0] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[0] = max(exit_rect.left, min(exit_rect.right - entity.size[0], entity.pos[0]))
                entity.pos[1] = exit_rect.top + offset
                # Entering from left (moving left), exit going DOWN from top edge
                # Take horizontal left velocity magnitude, convert to vertical DOWN velocity (preserve momentum)
                horizontal_speed = abs(old_velocity[0])
                # If no horizontal velocity, use vertical velocity or minimum
                if horizontal_speed == 0:
                    horizontal_speed = abs(old_velocity[1]) if abs(old_velocity[1]) > 0 else 2.0
                entity.velocity[0] = 0
                entity.velocity[1] = horizontal_speed  # Downward (positive Y) - launch downward with conserved momentum
            elif exit_edge == 'top':  # Exiting top edge (entering from top), exit from left edge going right
                entity.pos[0] = exit_rect.left + offset
                # Use relative_position to place entity at same position along the vertical edge
                # relative_position is along the top edge (horizontal), so we use it for vertical position
                entity.pos[1] = exit_rect.top + (relative_position * exit_rect.height) - entity.size[1] // 2
                # Clamp to ensure entity stays within portal bounds
                entity.pos[1] = max(exit_rect.top, min(exit_rect.bottom - entity.size[1], entity.pos[1]))
                # Entering from top (moving up), exit going RIGHT from left edge
                # Take vertical up velocity magnitude, convert to horizontal RIGHT velocity (preserve momentum)
                vertical_speed = abs(old_velocity[1])
                # If no vertical velocity, use horizontal velocity or minimum
                if vertical_speed == 0:
                    vertical_speed = abs(old_velocity[0]) if abs(old_velocity[0]) > 0 else 2.0
                entity.velocity[0] = vertical_speed  # Rightward (positive X) - launch right with conserved momentum
                entity.velocity[1] = 0
        
        # After teleportation, update last_pos to be outside the exit portal
        # This prevents immediate re-teleportation detection
        # We set it to a position just outside the entry edge
        if self.lock_type == 'left':  # red portal
            if exit_edge == 'left':  # Entered from right
                entity.last_pos[0] = exit_rect.right + 1
            elif exit_edge == 'right':  # Entered from left
                entity.last_pos[0] = exit_rect.left - entity.size[0] - 1
            elif exit_edge == 'top':  # Entered from bottom
                entity.last_pos[1] = exit_rect.bottom + 1
            elif exit_edge == 'bottom':  # Entered from top
                entity.last_pos[1] = exit_rect.top - entity.size[1] - 1
        elif self.lock_type == 'right':  # white portal
            if exit_edge == 'right':  # Entered from bottom
                entity.last_pos[1] = exit_rect.bottom + 1
            elif exit_edge == 'bottom':  # Entered from right
                entity.last_pos[0] = exit_rect.right + 1
            elif exit_edge == 'left':  # Entered from left, exits from top going down
                entity.last_pos[1] = exit_rect.top - entity.size[1] - 1
            elif exit_edge == 'top':  # Entered from top, exits from left going right
                entity.last_pos[0] = exit_rect.left - entity.size[0] - 1
        
        return True
    
    def render(self, surf, offset=(0, 0)):
        x = self.pos[0] - offset[0]
        y = self.pos[1] - offset[1]
        
        # Render portal sprite based on lock type
        if self.locked and self.lock_type:
            if self.lock_type == 'left' and self.red_animation:
                # red portal for left click
                portal_img = self.red_animation.img()
                # Scale image to portal size if needed
                if portal_img.get_width() != self.size or portal_img.get_height() != self.size:
                    portal_img = pygame.transform.scale(portal_img, (self.size, self.size))
                surf.blit(portal_img, (x, y))
            elif self.lock_type == 'right' and self.white_animation:
                # white portal for right click
                portal_img = self.white_animation.img()
                # Scale image to portal size if needed
                if portal_img.get_width() != self.size or portal_img.get_height() != self.size:
                    portal_img = pygame.transform.scale(portal_img, (self.size, self.size))
                surf.blit(portal_img, (x, y))
            else:
                # Fallback to old rectangle drawing if sprites not available
                pygame.draw.rect(surf, self.color, (x, y, self.size, self.size), self.thickness)
        else:
            # Unlocked portal - draw gray outline
            pygame.draw.rect(surf, self.color, (x, y, self.size, self.size), self.thickness)
