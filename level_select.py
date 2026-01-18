import os
import pygame
import glob
import math
from scripts.utils import load_images, Animation
from homepage import generate_level_with_gemini

class LevelSelect:
    def __init__(self):
        pygame.init()
        
        # Display setup (same as homepage/game)
        self.display = pygame.Surface((540, 380), pygame.SRCALPHA)
        self.screen = pygame.display.set_mode((960, 640))
        self.clock = pygame.time.Clock()
        
        # Show default cursor (game hides it, so we restore it here)
        pygame.mouse.set_visible(True)
        
        # Get game directory
        game_dir = os.path.dirname(os.path.abspath(__file__))
        maps_dir = os.path.join(game_dir, 'data', 'maps')
        
        # Background
        homepage_assets_dir = os.path.join(game_dir, 'data', 'homepage-assets')
        background_path = os.path.join(homepage_assets_dir, 'level_selection.png')
        background_raw = pygame.image.load(background_path).convert()
        self.background = pygame.transform.scale(background_raw, self.display.get_size())
        
        # Load portal animations
        portal_red_images = load_images('portal_red')
        portal_white_images = load_images('portal_white')
        self.portal_red_animation = Animation(portal_red_images, img_dur=5)
        self.portal_white_animation = Animation(portal_white_images, img_dur=5)
        self.portal_size = 64  # Size of portals in pixels
        
        # Fonts - Using Press Start 2P
        font_path_press_start = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
        self.font = pygame.font.Font(font_path_press_start, 8)
        self.title_font = pygame.font.Font(font_path_press_start, 16)  # Bigger title
        
        # Discover available levels
        self.standard_levels = []
        self.gemini_levels = []
        
        # Find standard levels (level1.json, level2.json, etc.)
        for level_file in sorted(glob.glob(os.path.join(maps_dir, 'level*.json'))):
            filename = os.path.basename(level_file)
            # Extract number from filename (e.g., "level5.json" -> 5)
            if filename.startswith('level') and filename.endswith('.json'):
                level_num_str = filename[5:-5]  # Remove "level" prefix and ".json" suffix
                if level_num_str.isdigit():
                    self.standard_levels.append((int(level_num_str), level_file))
        
        # Sort by level number
        self.standard_levels.sort(key=lambda x: x[0])
        
        # Find gemini levels (gemini1.json, gemini2.json, etc.)
        for level_file in sorted(glob.glob(os.path.join(maps_dir, 'gemini*.json'))):
            filename = os.path.basename(level_file)
            # Extract number from filename (e.g., "gemini5.json" -> 5)
            if filename.startswith('gemini') and filename.endswith('.json'):
                level_num_str = filename[6:-5]  # Remove "gemini" prefix and ".json" suffix
                if level_num_str.isdigit():
                    self.gemini_levels.append((int(level_num_str), level_file))
        
        # Sort by level number
        self.gemini_levels.sort(key=lambda x: x[0])
        
        # Layout configuration - two columns
        self.title_y = 15
        self.column_top_y = 70  # Start of columns (increased spacing from title)
        self.column_height = 200  # Height available for buttons (6 buttons)
        self.max_visible = 6  # Maximum buttons visible per column
        
        # Column positions
        column_width = 200
        column_gap = 60
        total_width = (column_width * 2) + column_gap
        start_x = (self.display.get_width() - total_width) // 2
        
        self.standard_column_x = start_x
        self.gemini_column_x = start_x + column_width + column_gap
        
        # Button layout
        self.button_width = 180
        self.button_height = 24
        self.button_gap = 8
        
        # Column background padding
        self.column_padding = 8  # Padding around buttons in gray background
        
        # Scroll offsets for each column
        self.standard_scroll = 0
        self.gemini_scroll = 0
        
        # Calculate max scroll for each column
        self._calculate_max_scrolls()
        
        # Generate button (in gemini column, below buttons)
        self.generate_button_width = 180
        self.generate_button_height = 28
        
        # Exit button
        self.exit_button_width = 100
        self.exit_button_height = 28
        self.exit_button_y = self.display.get_height() - self.exit_button_height - 10
        self.exit_button_rect = pygame.Rect(
            (self.display.get_width() - self.exit_button_width) // 2,
            self.exit_button_y,
            self.exit_button_width,
            self.exit_button_height
        )
        
        # Interactive state
        self.hovered_button = None  # Level path, "generate", or "exit"
        self.clicked_button = None
        self.click_anim_time = 0.0
        self.elapsed_time = 0.0
        
        # Button wiggle
        self.button_wiggle_phase = 0.0
        
        # Loading state
        self.is_loading = False
    
    def _calculate_max_scrolls(self):
        """Calculate maximum scroll offsets for each column"""
        button_spacing = self.button_height + self.button_gap
        total_standard_height = len(self.standard_levels) * button_spacing
        self.max_standard_scroll = max(0, total_standard_height - self.column_height)
        
        total_gemini_height = len(self.gemini_levels) * button_spacing
        self.max_gemini_scroll = max(0, total_gemini_height - self.column_height)
    
    def _get_visible_levels(self, levels, scroll, max_scroll):
        """Get the levels that should be visible based on scroll position"""
        if len(levels) <= self.max_visible:
            return levels, 0
        
        # Calculate which levels are visible
        button_spacing = self.button_height + self.button_gap
        start_index = int(scroll / button_spacing)
        end_index = min(start_index + self.max_visible, len(levels))
        
        return levels[start_index:end_index], start_index
    
    def _render_outlined(self, text, font, fg, outline, thickness):
        """Render text with outline"""
        surf = font.render(text, False, fg)
        outline_surf = font.render(text, False, outline)
        final = pygame.Surface((surf.get_width() + thickness * 2, surf.get_height() + thickness * 2), pygame.SRCALPHA)
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx * dx + dy * dy <= thickness * thickness:
                    final.blit(outline_surf, (thickness + dx, thickness + dy))
        final.blit(surf, (thickness, thickness))
        return final
    
    def update(self, dt):
        """Update animation state"""
        self.elapsed_time += dt
        self.button_wiggle_phase += dt * 1.8
        
        # Update portal animations
        self.portal_red_animation.update()
        self.portal_white_animation.update()
        
        # Update click animation
        if self.click_anim_time > 0:
            self.click_anim_time = max(0.0, self.click_anim_time - dt)
    
    def handle_scroll(self, x, y, scroll_delta):
        """Handle mouse wheel scrolling"""
        display_x = int((x / self.screen.get_width()) * self.display.get_width())
        display_y = int((y / self.screen.get_height()) * self.display.get_height())
        
        # Check if mouse is over standard column
        if self.standard_column_x <= display_x <= self.standard_column_x + self.button_width:
            if self.column_top_y <= display_y <= self.column_top_y + self.column_height:
                self.standard_scroll = max(0, min(self.max_standard_scroll, self.standard_scroll - scroll_delta))
        
        # Check if mouse is over gemini column
        elif self.gemini_column_x <= display_x <= self.gemini_column_x + self.button_width:
            if self.column_top_y <= display_y <= self.column_top_y + self.column_height:
                self.gemini_scroll = max(0, min(self.max_gemini_scroll, self.gemini_scroll - scroll_delta))
    
    def render(self):
        """Render the level selection screen"""
        self.display.fill((0, 0, 0))
        self.display.blit(self.background, (0, 0))
        
        # Title at top center
        title_surf = self._render_outlined("LEVEL SELECTION", self.title_font, (255, 255, 255), (0, 50, 120), 3)
        title_x = (self.display.get_width() - title_surf.get_width()) // 2
        self.display.blit(title_surf, (title_x, self.title_y))
        
        # Section headers (always show) - centered with their columns, same horizontal line
        standard_title_surf = self._render_outlined("Authored Levels", self.font, (255, 200, 50), (0, 50, 120), 2)
        standard_title_x = self.standard_column_x + (self.button_width - standard_title_surf.get_width()) // 2
        title_y = self.column_top_y - 20
        self.display.blit(standard_title_surf, (standard_title_x, title_y))
        
        gemini_title_surf = self._render_outlined("Gemini Levels", self.font, (255, 200, 50), (0, 50, 120), 2)
        gemini_title_x = self.gemini_column_x + (self.button_width - gemini_title_surf.get_width()) // 2
        self.display.blit(gemini_title_surf, (gemini_title_x, title_y))  # Same y position as standard title
        
        # Draw light gray background for column areas (with padding and spacing from titles)
        title_to_column_spacing = 5  # Space between category titles and gray squares (halved)
        bg_width = self.button_width + (self.column_padding * 2)
        bg_height = self.column_height + (self.column_padding * 2)
        bg_x_standard = self.standard_column_x - self.column_padding
        bg_x_gemini = self.gemini_column_x - self.column_padding
        bg_y = self.column_top_y + title_to_column_spacing  # Add spacing below titles
        
        # Draw backgrounds with rounded corners
        gray_bg = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        # Draw rounded rectangle
        pygame.draw.rect(gray_bg, (180, 180, 180), (0, 0, bg_width, bg_height), border_radius=8)
        gray_bg.set_alpha(180)  # Semi-transparent
        
        # Draw backgrounds
        self.display.blit(gray_bg, (bg_x_standard, bg_y))
        self.display.blit(gray_bg, (bg_x_gemini, bg_y))
        
        # No border outline - removed per user request
        
        # Add scroll indicators if content is scrollable
        if len(self.standard_levels) > self.max_visible:
            # Up arrow indicator at top
            indicator_y = bg_y + 3
            indicator_x = bg_x_standard + bg_width // 2
            pygame.draw.polygon(self.display, (150, 150, 150), [
                (indicator_x - 3, indicator_y + 5),
                (indicator_x, indicator_y),
                (indicator_x + 3, indicator_y + 5)
            ])
            # Down arrow indicator at bottom
            indicator_y_bottom = bg_y + bg_height - 8
            pygame.draw.polygon(self.display, (150, 150, 150), [
                (indicator_x - 3, indicator_y_bottom),
                (indicator_x, indicator_y_bottom + 5),
                (indicator_x + 3, indicator_y_bottom)
            ])
        
        if len(self.gemini_levels) > self.max_visible:
            # Up arrow indicator at top
            indicator_y = bg_y + 3
            indicator_x = bg_x_gemini + bg_width // 2
            pygame.draw.polygon(self.display, (150, 150, 150), [
                (indicator_x - 3, indicator_y + 5),
                (indicator_x, indicator_y),
                (indicator_x + 3, indicator_y + 5)
            ])
            # Down arrow indicator at bottom
            indicator_y_bottom = bg_y + bg_height - 8
            pygame.draw.polygon(self.display, (150, 150, 150), [
                (indicator_x - 3, indicator_y_bottom),
                (indicator_x, indicator_y_bottom + 5),
                (indicator_x + 3, indicator_y_bottom)
            ])
        
        # Get visible levels for each column
        visible_standard, standard_start_idx = self._get_visible_levels(self.standard_levels, self.standard_scroll, self.max_standard_scroll)
        visible_gemini, gemini_start_idx = self._get_visible_levels(self.gemini_levels, self.gemini_scroll, self.max_gemini_scroll)
        
        # Update column_top_y to match the actual button area inside the gray square (accounting for padding and spacing)
        actual_column_top_y = bg_y + self.column_padding
        
        # Draw standard level buttons (left column) with clipping
        button_spacing = self.button_height + self.button_gap
        # Clip area matches the gray background area (with padding)
        clip_rect_standard = pygame.Rect(bg_x_standard, bg_y, bg_width, bg_height)
        
        # Save current clip and set new clip for standard column
        old_clip = self.display.get_clip()
        self.display.set_clip(clip_rect_standard)
        
        for i, (level_num, level_path) in enumerate(visible_standard):
            actual_index = standard_start_idx + i
            button_y = actual_column_top_y + (actual_index * button_spacing) - self.standard_scroll
            button_rect = pygame.Rect(self.standard_column_x, button_y, self.button_width, self.button_height)
            
            # Only render if button is within or partially within the clip area
            if button_rect.colliderect(clip_rect_standard):
                self._draw_level_button(button_rect, level_path, "standard", level_num)
        
        # Restore clip and set new clip for gemini column
        # Clip area matches the gray background area (with padding)
        clip_rect_gemini = pygame.Rect(bg_x_gemini, bg_y, bg_width, bg_height)
        self.display.set_clip(clip_rect_gemini)
        
        for i, (level_num, level_path) in enumerate(visible_gemini):
            actual_index = gemini_start_idx + i
            button_y = actual_column_top_y + (actual_index * button_spacing) - self.gemini_scroll
            button_rect = pygame.Rect(self.gemini_column_x, button_y, self.button_width, self.button_height)
            
            # Only render if button is within or partially within the clip area
            if button_rect.colliderect(clip_rect_gemini):
                self._draw_level_button(button_rect, level_path, "gemini", level_num)
        
        # Restore original clip
        self.display.set_clip(old_clip)
        
        # Generate Level button (right column, below gray square)
        generate_button_y = bg_y + bg_height + 7  # Below the gray square (half spacing)
        generate_button_rect = pygame.Rect(self.gemini_column_x, generate_button_y, self.generate_button_width, self.generate_button_height)
        self._draw_generate_button(generate_button_rect)
        
        # Exit button at bottom
        self._draw_exit_button()
        
        # Loading overlay
        if self.is_loading:
            overlay = pygame.Surface(self.display.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.display.blit(overlay, (0, 0))
            
            loading_surface = self.font.render("Generating level...", False, (255, 255, 255))
            loading_x = (self.display.get_width() - loading_surface.get_width()) // 2
            loading_y = (self.display.get_height() - loading_surface.get_height()) // 2
            self.display.blit(loading_surface, (loading_x, loading_y))
    
    def _draw_level_button(self, button_rect, level_path, level_type, level_num):
        """Draw a level button"""
        # Check if hovered
        is_hovered = self.hovered_button == level_path
        is_clicked = self.clicked_button == level_path
        
        # Determine button styling based on type
        if level_type == "standard":
            # Make background color brighter when hovered
            if is_hovered:
                bg_color = (255, 220, 70)  # Brighter yellow when hovered
            else:
                bg_color = (255, 200, 50)  # Normal yellow
            text_color = (0, 50, 120)  # Blue
            button_label = f"Level {level_num}"
        else:  # gemini
            # Make background color brighter when hovered
            if is_hovered:
                bg_color = (130, 70, 180)  # Brighter purple when hovered
            else:
                bg_color = (100, 50, 150)  # Normal purple
            text_color = (255, 255, 255)  # White
            button_label = f"Gemini {level_num}"
        
        # Calculate scale for hover/click
        scale = 1.0
        if is_clicked and self.click_anim_time > 0:
            scale = 0.95
        elif is_hovered:
            scale = 1.05
        
        # Wiggle animation (continuous)
        wiggle_speed = 1.8
        wiggle_amount = 1.0
        button_phase = self.elapsed_time * wiggle_speed + (hash(level_path) % 100 * 0.1)
        wiggle_x = math.sin(button_phase) * wiggle_amount
        wiggle_y = math.cos(button_phase * 1.3) * wiggle_amount
        
        # Apply wiggle and scale
        center_x = button_rect.centerx + int(wiggle_x)
        center_y = button_rect.centery + int(wiggle_y)
        scaled_width = int(button_rect.width * scale)
        scaled_height = int(button_rect.height * scale)
        
        # Draw button
        button_surf = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, bg_color, (0, 0, scaled_width, scaled_height), border_radius=5)
        pygame.draw.rect(button_surf, (0, 50, 120), (0, 0, scaled_width, scaled_height), width=2, border_radius=5)
        
        # Draw text (without outline for readability)
        text_surf = self.font.render(button_label, False, text_color)
        text_x = (scaled_width - text_surf.get_width()) // 2
        text_y = (scaled_height - text_surf.get_height()) // 2
        button_surf.blit(text_surf, (text_x, text_y))
        
        self.display.blit(button_surf, (center_x - scaled_width // 2, center_y - scaled_height // 2))
    
    def _draw_generate_button(self, button_rect):
        """Draw the generate button"""
        is_generate_hovered = self.hovered_button == "generate"
        is_generate_clicked = self.clicked_button == "generate"
        
        generate_scale = 1.0
        if is_generate_clicked and self.click_anim_time > 0:
            generate_scale = 0.95
        elif is_generate_hovered:
            generate_scale = 1.05
        
        # Generate button wiggle
        generate_phase = self.elapsed_time * 1.8 + 200
        generate_wiggle_x = math.sin(generate_phase) * 1.0
        generate_wiggle_y = math.cos(generate_phase * 1.3) * 1.0
        
        generate_center_x = button_rect.centerx + int(generate_wiggle_x)
        generate_center_y = button_rect.centery + int(generate_wiggle_y)
        generate_scaled_width = int(button_rect.width * generate_scale)
        generate_scaled_height = int(button_rect.height * generate_scale)
        
        # Change background color on hover
        if is_generate_hovered:
            generate_bg_color = (130, 180, 255)  # Brighter blue when hovered
        else:
            generate_bg_color = (100, 150, 255)  # Normal light blue
        
        generate_surf = pygame.Surface((generate_scaled_width, generate_scaled_height), pygame.SRCALPHA)
        pygame.draw.rect(generate_surf, generate_bg_color, (0, 0, generate_scaled_width, generate_scaled_height), border_radius=5)
        pygame.draw.rect(generate_surf, (0, 50, 120), (0, 0, generate_scaled_width, generate_scaled_height), width=2, border_radius=5)
        
        generate_text_surf = self.font.render("Generate Level", False, (255, 255, 255))  # White text
        generate_text_x = (generate_scaled_width - generate_text_surf.get_width()) // 2
        generate_text_y = (generate_scaled_height - generate_text_surf.get_height()) // 2
        generate_surf.blit(generate_text_surf, (generate_text_x, generate_text_y))
        
        self.display.blit(generate_surf, (generate_center_x - generate_scaled_width // 2, generate_center_y - generate_scaled_height // 2))
    
    def _draw_exit_button(self):
        """Draw the exit button"""
        is_exit_hovered = self.hovered_button == "exit"
        is_exit_clicked = self.clicked_button == "exit"
        
        exit_scale = 1.0
        if is_exit_clicked and self.click_anim_time > 0:
            exit_scale = 0.95
        elif is_exit_hovered:
            exit_scale = 1.05
        
        # Exit button wiggle
        exit_phase = self.elapsed_time * 1.8 + 100
        exit_wiggle_x = math.sin(exit_phase) * 1.0
        exit_wiggle_y = math.cos(exit_phase * 1.3) * 1.0
        
        exit_center_x = self.exit_button_rect.centerx + int(exit_wiggle_x)
        exit_center_y = self.exit_button_rect.centery + int(exit_wiggle_y)
        exit_scaled_width = int(self.exit_button_rect.width * exit_scale)
        exit_scaled_height = int(self.exit_button_rect.height * exit_scale)
        
        # Change background color on hover
        if is_exit_hovered:
            exit_bg_color = (230, 40, 40)  # Brighter red when hovered
        else:
            exit_bg_color = (200, 20, 20)  # Normal red
        
        exit_surf = pygame.Surface((exit_scaled_width, exit_scaled_height), pygame.SRCALPHA)
        pygame.draw.rect(exit_surf, exit_bg_color, (0, 0, exit_scaled_width, exit_scaled_height), border_radius=5)
        pygame.draw.rect(exit_surf, (0, 50, 120), (0, 0, exit_scaled_width, exit_scaled_height), width=1, border_radius=5)  # Subtle dark blue outline
        
        exit_text_surf = self.font.render("BACK", False, (255, 255, 255))
        exit_text_x = (exit_scaled_width - exit_text_surf.get_width()) // 2
        exit_text_y = (exit_scaled_height - exit_text_surf.get_height()) // 2
        exit_surf.blit(exit_text_surf, (exit_text_x, exit_text_y))
        
        self.display.blit(exit_surf, (exit_center_x - exit_scaled_width // 2, exit_center_y - exit_scaled_height // 2))
    
    def update_hover(self, mouse_pos):
        """Update which button is being hovered"""
        display_x = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        display_y = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        display_pos = (display_x, display_y)
        
        self.hovered_button = None
        
        # Calculate actual column top y (matches render method calculation)
        title_to_column_spacing = 5
        bg_y = self.column_top_y + title_to_column_spacing
        actual_column_top_y = bg_y + self.column_padding
        
        # Check standard level buttons
        button_spacing = self.button_height + self.button_gap
        visible_standard, standard_start_idx = self._get_visible_levels(self.standard_levels, self.standard_scroll, self.max_standard_scroll)
        for i, (level_num, level_path) in enumerate(visible_standard):
            actual_index = standard_start_idx + i
            button_y = actual_column_top_y + (actual_index * button_spacing) - self.standard_scroll
            button_rect = pygame.Rect(self.standard_column_x, button_y, self.button_width, self.button_height)
            if button_rect.collidepoint(display_pos):
                self.hovered_button = level_path
                return
        
        # Check gemini level buttons
        visible_gemini, gemini_start_idx = self._get_visible_levels(self.gemini_levels, self.gemini_scroll, self.max_gemini_scroll)
        for i, (level_num, level_path) in enumerate(visible_gemini):
            actual_index = gemini_start_idx + i
            button_y = actual_column_top_y + (actual_index * button_spacing) - self.gemini_scroll
            button_rect = pygame.Rect(self.gemini_column_x, button_y, self.button_width, self.button_height)
            if button_rect.collidepoint(display_pos):
                self.hovered_button = level_path
                return
        
        # Check generate button (position calculated based on gray square position)
        title_to_column_spacing = 5
        bg_y_hover = self.column_top_y + title_to_column_spacing
        bg_height_hover = self.column_height + (self.column_padding * 2)
        generate_button_y = bg_y_hover + bg_height_hover + 7  # Half spacing
        generate_button_rect = pygame.Rect(self.gemini_column_x, generate_button_y, self.generate_button_width, self.generate_button_height)
        if generate_button_rect.collidepoint(display_pos):
            self.hovered_button = "generate"
            return
        
        # Check exit button
        if self.exit_button_rect.collidepoint(display_pos):
            self.hovered_button = "exit"
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks, return level path or "BACK" or "GENERATE_GEMINI" or None"""
        display_x = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        display_y = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        display_pos = (display_x, display_y)
        
        # Visual feedback
        self.clicked_button = self.hovered_button
        self.click_anim_time = 0.15
        
        # Calculate actual column top y (matches render method calculation)
        title_to_column_spacing = 5
        bg_y = self.column_top_y + title_to_column_spacing
        actual_column_top_y = bg_y + self.column_padding
        
        # Check standard level buttons
        button_spacing = self.button_height + self.button_gap
        visible_standard, standard_start_idx = self._get_visible_levels(self.standard_levels, self.standard_scroll, self.max_standard_scroll)
        for i, (level_num, level_path) in enumerate(visible_standard):
            actual_index = standard_start_idx + i
            button_y = actual_column_top_y + (actual_index * button_spacing) - self.standard_scroll
            button_rect = pygame.Rect(self.standard_column_x, button_y, self.button_width, self.button_height)
            if button_rect.collidepoint(display_pos):
                return level_path
        
        # Check gemini level buttons
        visible_gemini, gemini_start_idx = self._get_visible_levels(self.gemini_levels, self.gemini_scroll, self.max_gemini_scroll)
        for i, (level_num, level_path) in enumerate(visible_gemini):
            actual_index = gemini_start_idx + i
            button_y = actual_column_top_y + (actual_index * button_spacing) - self.gemini_scroll
            button_rect = pygame.Rect(self.gemini_column_x, button_y, self.button_width, self.button_height)
            if button_rect.collidepoint(display_pos):
                return level_path
        
        # Check generate button (position calculated based on gray square position)
        title_to_column_spacing = 5
        bg_y = self.column_top_y + title_to_column_spacing
        bg_height = self.column_height + (self.column_padding * 2)
        generate_button_y = bg_y + bg_height + 7  # Half spacing
        generate_button_rect = pygame.Rect(self.gemini_column_x, generate_button_y, self.generate_button_width, self.generate_button_height)
        if generate_button_rect.collidepoint(display_pos):
            return "GENERATE_GEMINI"
        
        # Check exit button
        if self.exit_button_rect.collidepoint(display_pos):
            return "BACK"
        
        return None


def run_level_select():
    """
    Main level selection loop.
    
    Returns:
        str: Path to selected level, or "BACK" to return to homepage
    """
    level_select = LevelSelect()
    
    while True:
        dt = level_select.clock.tick(60) / 1000.0
        level_select.update(dt)
        
        # Track mouse position continuously for hover
        level_select.update_hover(pygame.mouse.get_pos())
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            
            if event.type == pygame.MOUSEMOTION:
                level_select.update_hover(event.pos)
            
            if event.type == pygame.MOUSEWHEEL:
                # Scroll when mouse wheel is used
                scroll_delta = event.y * 30  # Scroll speed
                mouse_pos = pygame.mouse.get_pos()
                level_select.handle_scroll(mouse_pos[0], mouse_pos[1], scroll_delta)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                choice = level_select.handle_click(event.pos)
                
                if choice == "GENERATE_GEMINI":
                    level_select.is_loading = True
                    
                    level_select.render()
                    scaled_display = pygame.transform.scale(level_select.display, level_select.screen.get_size())
                    level_select.screen.blit(scaled_display, (0, 0))
                    pygame.display.update()
                    
                    generated_path = generate_level_with_gemini()
                    
                    level_select.is_loading = False
                    
                    if generated_path:
                        # Reload gemini levels to include the new one
                        level_select.gemini_levels = []
                        maps_dir = os.path.dirname(os.path.abspath(__file__))
                        maps_dir = os.path.join(maps_dir, 'data', 'maps')
                        for level_file in sorted(glob.glob(os.path.join(maps_dir, 'gemini*.json'))):
                            filename = os.path.basename(level_file)
                            if filename.startswith('gemini') and filename.endswith('.json'):
                                level_num_str = filename[6:-5]
                                if level_num_str.isdigit():
                                    level_select.gemini_levels.append((int(level_num_str), level_file))
                        level_select.gemini_levels.sort(key=lambda x: x[0])
                        level_select._calculate_max_scrolls()
                    else:
                        print("Failed to generate level. Please check your GEMINI_API_KEY environment variable.")
                    continue
                
                elif choice:
                    return choice
        
        level_select.render()
        scaled_display = pygame.transform.scale(level_select.display, level_select.screen.get_size())
        level_select.screen.blit(scaled_display, (0, 0))
        pygame.display.update()


if __name__ == "__main__":
    choice = run_level_select()
    print(f"Selected: {choice}")
