"""
Homepage/Title Screen for The Time I Was Reincarnated As A Teleporting Goat In A 2D Puzzle Platformer

This file is runnable separately right now for testing purposes.
TODO: Integrate this with game.py to replace the direct game start.

The homepage handles:
- Background rendering
- Title animation: type line 1 -> splash reveal "TELEPORTING GOAT" -> type line 3
- Goat entrance and sprite switching
- Speech bubble animation
- Button interactions (Start Game, Select Level, Generate Level)
- Returns user choice as a string to the main controller
"""

import os
import pygame
import math
import json
import random
from google import genai

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass


class Homepage:
    def __init__(self):
        pygame.init()

        # Window and display configuration (matching game.py style)
        pygame.display.set_caption('Portal Puzzle - Homepage')
        self.screen = pygame.display.set_mode((960, 640))
        self.display = pygame.Surface((540, 380), pygame.SRCALPHA)

        self.clock = pygame.time.Clock()

        # Get paths
        game_dir = os.path.dirname(os.path.abspath(__file__))
        homepage_assets_dir = os.path.join(game_dir, 'data', 'homepage-assets')

        # Load assets
        self.background = pygame.image.load(
            os.path.join(homepage_assets_dir, 'home-bg.png')
        ).convert()
        self.background = pygame.transform.scale(self.background, (540, 380))

        # Load goat sprites and scale them down to fit better on screen
        shocked_goat_raw = pygame.image.load(
            os.path.join(homepage_assets_dir, 'shocked_goat.png')
        ).convert_alpha()
        shocked_goat_scale = 0.25
        shocked_goat_width = int(shocked_goat_raw.get_width() * shocked_goat_scale)
        shocked_goat_height = int(shocked_goat_raw.get_height() * shocked_goat_scale)
        self.shocked_goat = pygame.transform.scale(shocked_goat_raw, (shocked_goat_width, shocked_goat_height))

        surprised_goat_raw = pygame.image.load(
            os.path.join(homepage_assets_dir, 'surprised_goat.png')
        ).convert_alpha()
        surprised_goat_scale = 0.18
        surprised_goat_width = int(surprised_goat_raw.get_width() * surprised_goat_scale)
        surprised_goat_height = int(surprised_goat_raw.get_height() * surprised_goat_scale)
        self.surprised_goat = pygame.transform.scale(surprised_goat_raw, (surprised_goat_width, surprised_goat_height))

        # Goat target position (bottom-right)
        goat_margin_right = 5
        goat_offset_down = 17
        self.goat_target_pos = [
            self.display.get_width() - surprised_goat_width - goat_margin_right,
            self.display.get_height() - surprised_goat_height + goat_offset_down
        ]
        self.goat_pos = [
            self.goat_target_pos[0],
            self.display.get_height()
        ]

        # Speech bubble
        speech_bubble_raw = pygame.image.load(
            os.path.join(homepage_assets_dir, 'speech_bubble.png')
        ).convert_alpha()
        bubble_scale = 0.18
        bubble_width = int(speech_bubble_raw.get_width() * bubble_scale)
        bubble_height = int(speech_bubble_raw.get_height() * bubble_scale)
        self.speech_bubble = pygame.transform.scale(speech_bubble_raw, (bubble_width, bubble_height))

        # Fonts - Using Press Start 2P for title and buttons
        font_path_press_start = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
        self.font = pygame.font.Font(font_path_press_start, 8)          # buttons / small text
        self.button_font = pygame.font.Font(font_path_press_start, 8)   # button text
        self.title_font_small = pygame.font.Font(font_path_press_start, 14)  # line 1 / line 3
        self.title_font_big = pygame.font.Font(font_path_press_start, 20)    # "TELEPORTING GOAT"

        # Animation state
        self.elapsed_time = 0.0

        # -----------------------------
        # TITLE ANIMATION (NEW)
        # type line1 -> splash mid -> type line3
        # -----------------------------
        self.phase = "title_line1"

        self.title_line1 = "THE TIME I REINCARNATED AS A"
        self.title_mid = "TELEPORTING GOAT"
        self.title_line3 = "IN A 2D PUZZLE PLATFORMER"

        # Title layout
        self.title_y = 30  # Moved up from 46
        self.first_gap = 20  # Spacing between line 1 and line 2 (smaller)
        self.line_gap = 28  # Spacing between line 2 and line 3

        # Pre-render title surfaces once with matching colors
        # Lines 1 & 3: white with light blue highlight, dark blue outline
        # Middle: yellow-orange, thick dark blue outline
        self.surf_line1 = self._render_outlined(self.title_line1, self.title_font_small, fg=(255, 255, 255), outline=(0, 50, 120), thickness=3)
        self.surf_mid = self._render_outlined(self.title_mid, self.title_font_big, fg=(255, 200, 50), outline=(0, 50, 120), thickness=4)
        self.surf_line3 = self._render_outlined(self.title_line3, self.title_font_small, fg=(255, 255, 255), outline=(0, 50, 120), thickness=3)

        # Center the title block
        self.rect_line1 = self.surf_line1.get_rect(midtop=(self.display.get_width() // 2, self.title_y))
        self.rect_mid = self.surf_mid.get_rect(midtop=(self.display.get_width() // 2, self.title_y + self.first_gap))
        self.rect_line3 = self.surf_line3.get_rect(midtop=(self.display.get_width() // 2, self.title_y + self.first_gap + self.line_gap))

        # Typewriter reveal widths
        self.reveal1 = 0
        self.reveal3 = 0
        self.type_speed_px = 900  # pixels per second reveal rate

        # Splash config
        self.splash_time = 0.55
        self.hold_time = 0.12
        self.phase_timer = 0.0

        # Screen shake for splash
        self.shake = 0.0

        # Confetti particles for the splash (optional but "super extra")
        self.particles = []

        # Goat animation
        self.goat_entrance_speed = 150.0
        self.goat_entrance_start_time = 0.0
        self.goat_is_visible = False
        self.goat_surprised = False
        self.goat_surprised_start_time = 0.0

        # Speech bubble
        self.shocked_offset = (-62, -35)
        self.speech_bubble_visible = False
        self.speech_bubble_start_time = 0.0
        self.wiggle_trigger_time = 0.0  # When to trigger wiggle after bubble appears

        # Button states
        self.show_start_button = True
        self.show_menu_buttons = False

        # Loading state
        self.is_loading = False
        self.loading_text = "Generating level..."

        # Button definitions
        # Position buttons under the title block, centered like title
        title_block_height = (self.line_gap * 3) + 6
        button_y = self.title_y + title_block_height + 3  # Spacing from title

        button_width = 130
        button_padding = 4  # Vertical padding
        button_height = 20 + (button_padding * 2)  # Base height + padding
        button_gap = 15  # Gap between buttons
        
        # Button interaction state
        self.mouse_pos = (0, 0)
        self.hovered_button = None  # "start", "exit", "select_level", "generate_level", or None
        self.clicked_button = None  # Same as above, cleared after click
        self.click_anim_time = 0.0  # Time since click for visual feedback
        
        # Calculate total width of both buttons + gap
        total_button_width = (button_width * 2) + button_gap
        # Center the button group
        button_group_x = (self.display.get_width() - total_button_width) // 2
        
        # Start button (yellow background, blue outline, yellow text)
        self.start_button_rect = pygame.Rect(button_group_x, button_y, button_width, button_height)
        
        # Exit button (red background, blue outline, white text)
        exit_button_x = button_group_x + button_width + button_gap
        self.exit_button_rect = pygame.Rect(exit_button_x, button_y, button_width, button_height)
        
        # Menu buttons (keep for Select Level, Generate Level)
        self.select_level_button_rect = pygame.Rect(button_group_x, button_y, button_width, button_height)
        self.generate_level_button_rect = pygame.Rect(button_group_x, button_y + button_height + 5, button_width, button_height)

        # Timing constants (kept)
        self.GOAT_ENTRANCE_DELAY = 0.7
        self.GOAT_SURPRISED_DELAY = 1.0
        self.SPEECH_BUBBLE_DELAY = 0.3

    # -----------------------------
    # Helpers
    # -----------------------------
    def _render_outlined(self, text, font, fg=(255, 255, 255), outline=(0, 0, 0), thickness=2):
        base = font.render(text, False, fg).convert_alpha()
        w, h = base.get_size()
        surf = pygame.Surface((w + thickness * 2, h + thickness * 2), pygame.SRCALPHA)

        # Outline "stamp"
        for ox in range(-thickness, thickness + 1):
            for oy in range(-thickness, thickness + 1):
                if ox == 0 and oy == 0:
                    continue
                # small circle-ish mask
                if ox * ox + oy * oy <= thickness * thickness:
                    s = font.render(text, False, outline).convert_alpha()
                    surf.blit(s, (ox + thickness, oy + thickness))

        surf.blit(base, (thickness, thickness))
        return surf

    def _spawn_confetti(self, center, n=26):
        cx, cy = center
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(140, 420)
            self.particles.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd - 140,
                "life": random.uniform(0.35, 0.85),
            })

    def _update_particles(self, dt):
        g = 900
        for p in self.particles:
            p["life"] -= dt
            p["vy"] += g * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= (0.98 ** (dt * 60))
        self.particles[:] = [p for p in self.particles if p["life"] > 0]

    def _draw_particles(self):
        for p in self.particles:
            pygame.draw.rect(self.display, (255, 255, 255), (int(p["x"]), int(p["y"]), 3, 3))

    # -----------------------------
    # Update / Render
    # -----------------------------
    def update(self, dt):
        """Update animation state based on delta time"""
        self.elapsed_time += dt

        # Confetti always updates
        self._update_particles(dt)

        # Decay shake (faster decay for quick wiggle effect)
        self.shake = max(0.0, self.shake - 60.0 * dt)  # Faster decay for quick wiggle

        # Update click animation
        if self.click_anim_time > 0:
            self.click_anim_time = max(0.0, self.click_anim_time - dt)

        # -----------------------------
        # TITLE PHASES
        # -----------------------------
        if self.phase.startswith("title"):
            self.phase_timer += dt

        # 1) TYPE LINE 1
        if self.phase == "title_line1":
            self.reveal1 = min(self.surf_line1.get_width(), self.reveal1 + int(self.type_speed_px * dt))
            if self.reveal1 >= self.surf_line1.get_width():
                self.phase = "title_hold_before_splash"
                self.phase_timer = 0.0

        # 2) HOLD
        elif self.phase == "title_hold_before_splash":
            if self.phase_timer >= self.hold_time:
                self.phase = "title_splash"
                self.phase_timer = 0.0
                self.shake = 10.0
                self._spawn_confetti(self.rect_mid.center, n=32)

        # 3) SPLASH MID
        elif self.phase == "title_splash":
            if self.phase_timer >= self.splash_time:
                self.phase = "title_hold_after_splash"
                self.phase_timer = 0.0

        # 4) HOLD
        elif self.phase == "title_hold_after_splash":
            if self.phase_timer >= self.hold_time:
                self.phase = "title_line3"
                self.phase_timer = 0.0

        # 5) TYPE LINE 3
        elif self.phase == "title_line3":
            self.reveal3 = min(self.surf_line3.get_width(), self.reveal3 + int(self.type_speed_px * dt))
            if self.reveal3 >= self.surf_line3.get_width():
                # Title finished -> goat entrance
                self.phase = "goat_entrance"
                self.goat_entrance_start_time = self.elapsed_time + self.GOAT_ENTRANCE_DELAY

        # -----------------------------
        # Goat entrance
        # -----------------------------
        if self.phase == "goat_entrance":
            if self.elapsed_time >= self.goat_entrance_start_time:
                if not self.goat_is_visible:
                    self.goat_is_visible = True

                entrance_elapsed = self.elapsed_time - self.goat_entrance_start_time
                entrance_progress = min(entrance_elapsed / 0.65, 1.0)

                if entrance_progress >= 1.0:
                    self.goat_pos = self.goat_target_pos.copy()
                    self.phase = "goat_surprised"
                    self.goat_surprised_start_time = self.elapsed_time + self.GOAT_SURPRISED_DELAY
                else:
                    start_x = self.display.get_width() + 30
                    start_y = self.display.get_height() + 30
                    target_x, target_y = self.goat_target_pos

                    self.goat_pos[0] = start_x + (target_x - start_x) * entrance_progress
                    self.goat_pos[1] = start_y + (target_y - start_y) * entrance_progress

        # Goat becomes surprised
        if self.phase == "goat_surprised":
            if self.elapsed_time >= self.goat_surprised_start_time:
                self.goat_surprised = True
                self.phase = "speech_bubble"
                self.speech_bubble_start_time = self.elapsed_time + self.SPEECH_BUBBLE_DELAY

        # Speech bubble appears
        if self.phase == "speech_bubble":
            if self.elapsed_time >= self.speech_bubble_start_time:
                self.speech_bubble_visible = True
                self.phase = "idle"
                # Schedule wiggle to trigger slightly after bubble appears (immediate)
                self.wiggle_trigger_time = self.elapsed_time
        
        # Trigger quick wiggle slightly after speech bubble appears
        if self.speech_bubble_visible and self.wiggle_trigger_time > 0:
            if self.elapsed_time >= self.wiggle_trigger_time:
                self.shake = 4.0  # Quick wiggle intensity
                self.wiggle_trigger_time = 0.0  # Reset to prevent retriggering

    def render(self):
        """Render all visuals to the pixel canvas"""
        self.display.fill((0, 0, 0))
        self.display.blit(self.background, (0, 0))

        # Apply shake offset (only during splash)
        sx = int(random.uniform(-self.shake, self.shake)) if self.shake > 0 else 0
        sy = int(random.uniform(-self.shake, self.shake)) if self.shake > 0 else 0

        # -----------------------------
        # Draw title
        # -----------------------------
        # LINE 1 crop reveal
        if self.reveal1 > 0:
            crop1 = pygame.Rect(0, 0, self.reveal1, self.surf_line1.get_height())
            self.display.blit(self.surf_line1, (self.rect_line1.x + sx, self.rect_line1.y + sy), area=crop1)

        # MID splash
        if self.phase in ("title_splash", "title_hold_after_splash", "title_line3", "goat_entrance", "goat_surprised", "speech_bubble", "idle"):
            u = 1.0
            if self.phase == "title_splash":
                u = min(1.0, self.phase_timer / self.splash_time)

            # nice pop + settle
            pop = 0.70 + 0.55 * math.sin(min(1.0, u) * math.pi)  # up to ~1.25
            settle = 1.0 + 0.12 * math.sin(min(1.0, u) * math.pi) * (1.0 - u)
            scale = (pop * 0.35 + settle * 0.65)

            rot = (math.sin(u * math.pi * 2.2) * 6.0) * (1.0 - u)

            mid_surf = pygame.transform.rotozoom(self.surf_mid, rot, scale)
            r = mid_surf.get_rect(center=(self.rect_mid.centerx + sx, self.rect_mid.centery + sy))
            self.display.blit(mid_surf, r)

        # LINE 3 crop reveal
        if self.phase in ("title_line3", "goat_entrance", "goat_surprised", "speech_bubble", "idle") and self.reveal3 > 0:
            crop3 = pygame.Rect(0, 0, self.reveal3, self.surf_line3.get_height())
            self.display.blit(self.surf_line3, (self.rect_line3.x + sx, self.rect_line3.y + sy), area=crop3)

        # Confetti particles
        self._draw_particles()

        # -----------------------------
        # Draw goat
        # -----------------------------
        if self.goat_is_visible:
            current_goat_sprite = self.shocked_goat if self.goat_surprised else self.surprised_goat
            goat_x = int(self.goat_pos[0])
            goat_y = int(self.goat_pos[1])
            if self.goat_surprised:
                ox, oy = self.shocked_offset
                goat_x += ox
                goat_y += oy
            self.display.blit(current_goat_sprite, (goat_x, goat_y))

        # Speech bubble
        if self.speech_bubble_visible and self.goat_is_visible:
            bubble_x = goat_x - 70
            bubble_y = goat_y - self.speech_bubble.get_height() + 110
            bubble_x = max(5, min(bubble_x, self.display.get_width() - self.speech_bubble.get_width() - 5))
            bubble_y = max(5, bubble_y)
            self.display.blit(self.speech_bubble, (bubble_x, bubble_y))

        # -----------------------------
        # Buttons
        # -----------------------------
        def draw_button(rect, button_id, text, bg_color, text_color, outline_color=(0, 50, 120)):
            # Check if hovering
            is_hovered = (self.hovered_button == button_id)
            is_clicked = (self.clicked_button == button_id and self.click_anim_time > 0)
            
            # Change background color on hover (similar to level buttons)
            if is_hovered:
                # Brighten the color based on button type
                if button_id == "exit":
                    # Exit button: brighter red
                    bg_color = (230, 40, 40)  # Brighter red when hovered
                elif button_id == "start" or bg_color == (255, 200, 50):  # Start button or yellow buttons
                    # Yellow buttons: brighter yellow
                    bg_color = (255, 220, 70)  # Brighter yellow when hovered
            
            # Calculate scale (1.05 on hover, 0.95 on click for feedback)
            scale = 1.0
            if is_clicked:
                scale = 0.95  # Slight scale down on click
            elif is_hovered and button_id != "start":  # Start button doesn't scale
                scale = 1.05  # Scale up 5% on hover
            
            # Apply scale to rect
            scaled_width = int(rect.width * scale)
            scaled_height = int(rect.height * scale)
            scaled_x = rect.centerx - scaled_width // 2
            scaled_y = rect.centery - scaled_height // 2
            scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
            
            border_radius = 5  # Rounded corners
            # Draw button background with rounded corners
            pygame.draw.rect(self.display, bg_color, scaled_rect, border_radius=border_radius)
            # Draw blue outline with rounded corners
            pygame.draw.rect(self.display, outline_color, scaled_rect, 2, border_radius=border_radius)
            
            # Render text with smaller button font (size 6)
            button_text_surf = self.button_font.render(text, False, text_color)
            
            # Calculate centered text position
            text_x = scaled_rect.centerx - button_text_surf.get_width() // 2
            text_y = scaled_rect.centery - button_text_surf.get_height() // 2
            
            # Draw text
            self.display.blit(button_text_surf, (text_x, text_y))

        # Only show buttons after title animation completes
        # Title is complete when we're past the title phases
        title_complete = self.phase not in ("title_line1", "title_hold_before_splash", "title_splash", "title_hold_after_splash", "title_line3")
        
        if title_complete:
            # Exit button: red background, white text, blue outline
            draw_button(self.exit_button_rect, "exit", "Exit", (200, 20, 20), (255, 255, 255))

            if self.show_start_button:
                # Start button: yellow background, blue text, blue outline
                draw_button(self.start_button_rect, "start", "Start Game", (255, 200, 50), (0, 50, 120))

        if self.show_menu_buttons:
            draw_button(self.select_level_button_rect, "select_level", "Select Level", (255, 200, 50), (0, 50, 120))

            generate_rect = pygame.Rect(
                self.select_level_button_rect.x,
                self.select_level_button_rect.y + self.select_level_button_rect.height + 5,
                self.select_level_button_rect.width,
                self.select_level_button_rect.height
            )
            draw_button(generate_rect, "generate_level", "Generate Level", (255, 200, 50), (0, 50, 120))
            self.generate_level_button_rect = generate_rect

        # Loading overlay
        if self.is_loading:
            overlay = pygame.Surface(self.display.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.display.blit(overlay, (0, 0))

            loading_surface = self.font.render(self.loading_text, False, (255, 255, 255))
            loading_x = self.display.get_width() // 2 - loading_surface.get_width() // 2
            loading_y = self.display.get_height() // 2 - loading_surface.get_height() // 2
            self.display.blit(loading_surface, (loading_x, loading_y))

    def update_hover(self, mouse_pos):
        """Update which button is being hovered"""
        # Only detect hover if title animation is complete
        title_complete = self.phase not in ("title_line1", "title_hold_before_splash", "title_splash", "title_hold_after_splash", "title_line3")
        if not title_complete:
            self.hovered_button = None
            return
        
        self.mouse_pos = mouse_pos
        display_x = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        display_y = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        display_pos = (display_x, display_y)

        self.hovered_button = None

        # Check exit button
        if self.exit_button_rect.collidepoint(display_pos):
            self.hovered_button = "exit"
            return

        if self.show_start_button and self.start_button_rect.collidepoint(display_pos):
            self.hovered_button = "start"
            return

        if self.show_menu_buttons:
            if self.select_level_button_rect.collidepoint(display_pos):
                self.hovered_button = "select_level"
                return
            if self.generate_level_button_rect.collidepoint(display_pos):
                self.hovered_button = "generate_level"
                return

    def handle_click(self, mouse_pos):
        """Handle mouse clicks, return choice string or None"""
        if self.is_loading:
            return None

        # Only handle clicks if title animation is complete
        title_complete = self.phase not in ("title_line1", "title_hold_before_splash", "title_splash", "title_hold_after_splash", "title_line3")
        if not title_complete:
            return None

        display_x = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        display_y = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        display_pos = (display_x, display_y)

        # Visual feedback - set clicked button briefly
        self.clicked_button = self.hovered_button
        self.click_anim_time = 0.15  # Click animation duration

        # Check exit button
        if self.exit_button_rect.collidepoint(display_pos):
            return "QUIT"

        if self.show_start_button and self.start_button_rect.collidepoint(display_pos):
            return "SELECT_LEVEL"

        if self.show_menu_buttons and self.select_level_button_rect.collidepoint(display_pos):
            return "SELECT_LEVEL"

        if self.show_menu_buttons and self.generate_level_button_rect.collidepoint(display_pos):
            return "GENERATE_LEVEL_START"

        return None


def generate_level_with_gemini(difficulty="medium", theme="classic puzzle"):
    """
    Generate a level using the Gemini API.

    Args:
        difficulty: "easy", "medium", or "hard"
        theme: A theme description for the level

    Returns:
        str: Path to the generated level JSON file, or None if generation failed
    """
    try:
        client = genai.Client()

        prompt = f"""You are a level designer for a 2D puzzle platformer with a unique portal mechanic. The player can place two linked portals - one always surrounds the player, and one follows the cursor. When the player enters one portal, they teleport to the other.

**GAME MECHANICS:**
- Player can place a portal at their position and at the cursor position
- Walking into one portal teleports you to the other
- Portals are 64x64 pixels (4x4 tiles)
- Player can push crates through portals
- Springs launch the player upward
- Spikes kill the player (can be rotated: 0°=up, 90°=right, 180°=down, 270°=left)
- Keys must be collected before doors can be used
- "noportalzone" tiles block portal placement in certain areas

**MAP FORMAT:**
- JSON with "tilemap", "tile_size": 16, and "offgrid" array
- Map bounds: x from 0 to 33, y from 0 to 23 (34x24 tiles, 544x384 pixels)
- Tile position format: "x;y" as key, with {{"type": "...", "variant": N, "pos": [x, y]}}

**TILE TYPES:**
- "grass" - solid ground (variants 0-8 for edges/fills)
- "stone" - solid walls (variants 0-8 for edges/fills)
- "noportalzone" - blocks portal placement (variant 0)
- "spikes" - kills player, add "rotation": 0/90/180/270 (variant 0)
- "spawners" - variant 0 = player spawn point

**OFFGRID ELEMENTS (in "offgrid" array):**
- Crates: {{"type": "spawners", "variant": 1, "pos": [x, y]}}
- Springs: {{"type": "spawners", "variant": 3, "pos": [x, y]}}
- Keys: {{"type": "key", "variant": 0, "pos": [x, y]}}
- Doors: {{"type": "door", "variant": 0, "pos": [x, y]}}

**PUZZLE DESIGN PRINCIPLES:**
1. The core mechanic is placing one portal on yourself and one at the cursor, then walking through
2. Good puzzles require the player to think about WHERE to place the cursor portal
3. Use noportalzones strategically to limit where portals can be placed
4. Create gaps the player cannot jump across but CAN portal across
5. Use vertical sections where the player must portal up/down
6. Crates can be pushed through portals to reach buttons or block hazards
7. Springs can launch players into otherwise unreachable areas

**OUTPUT FORMAT:**
Generate a complete, valid JSON map. Include:
1. Solid borders (grass/stone walls around edges)
2. One player spawn point (spawners variant 0)
3. One door and one key
4. At least one puzzle element (noportalzone, gap, vertical challenge)
5. Make sure the puzzle is solvable using the portal mechanic

Generate a [DIFFICULTY: {difficulty}] puzzle map with the theme: {theme}

Return ONLY the JSON object, no markdown formatting, no code blocks, just the raw JSON starting with {{ and ending with }}.
Increase the door's x and y position by one."""

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        response_text = response.text.strip()

        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])

        response_text = response_text.strip()

        game_dir = os.path.dirname(os.path.abspath(__file__))
        maps_dir = os.path.join(game_dir, 'data', 'maps')
        
        # Find the next available numbered filename
        counter = 1
        while True:
            filename = f'gemini{counter}.json'
            generated_map_path = os.path.join(maps_dir, filename)
            if not os.path.exists(generated_map_path):
                break
            counter += 1
        
        # Save the raw JSON response to file
        with open(generated_map_path, 'w', encoding='utf-8') as f:
            f.write(response_text)

        print(f"Level JSON response saved to: {generated_map_path}")
        return generated_map_path

    except Exception as e:
        print(f"Error generating level with Gemini API: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_homepage():
    """
    Main homepage loop. Handles animations and button interactions.

    Returns:
        str: User's choice - "SELECT_LEVEL", "GENERATE_LEVEL", or "QUIT"
    """
    homepage = Homepage()

    while True:
        dt = homepage.clock.tick(60) / 1000.0
        homepage.update(dt)

        # Track mouse position continuously for hover
        homepage.update_hover(pygame.mouse.get_pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            # Track mouse position for hover detection
            if event.type == pygame.MOUSEMOTION:
                homepage.update_hover(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                choice = homepage.handle_click(event.pos)

                if choice == "GENERATE_LEVEL_START":
                    homepage.is_loading = True

                    homepage.render()
                    scaled_display = pygame.transform.scale(homepage.display, homepage.screen.get_size())
                    homepage.screen.blit(scaled_display, (0, 0))
                    pygame.display.update()

                    generated_path = generate_level_with_gemini()

                    homepage.is_loading = False

                    if generated_path:
                        return "GENERATE_LEVEL"
                    else:
                        print("Failed to generate level. Please check your GEMINI_API_KEY environment variable.")
                        continue

                elif choice:
                    return choice

        homepage.render()
        scaled_display = pygame.transform.scale(homepage.display, homepage.screen.get_size())
        homepage.screen.blit(scaled_display, (0, 0))
        pygame.display.update()


if __name__ == "__main__":
    choice = run_homepage()
    print(f"Homepage returned: {choice}")
