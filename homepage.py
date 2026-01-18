"""
Homepage/Title Screen for The Time I Was Reincarnated As A Teleporting Goat In A 2D Puzzle Platformer

This file is runnable separately right now for testing purposes.
TODO: Integrate this with game.py to replace the direct game start.

The homepage handles:
- Background rendering
- Typing animation for title
- Goat entrance and sprite switching
- Speech bubble animation
- Button interactions (Start Game, Select Level, Generate Level)
- Returns user choice as a string to the main controller
"""

import os
import pygame
import math
import json
from google import genai
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    # python-dotenv not installed, but that's okay - can still use environment variables directly
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
            os.path.join(homepage_assets_dir, 'home-bg.jpg')
        ).convert()
        # Scale background to match display size
        self.background = pygame.transform.scale(self.background, (540, 380))
        
        # Load goat sprites and scale them down to fit better on screen
        shocked_goat_raw = pygame.image.load(
            os.path.join(homepage_assets_dir, 'shocked_goat.png')
        ).convert_alpha()
        # Scale goat to slightly smaller size
        goat_scale = 0.18
        goat_width = int(shocked_goat_raw.get_width() * goat_scale)
        goat_height = int(shocked_goat_raw.get_height() * goat_scale)
        self.shocked_goat = pygame.transform.scale(shocked_goat_raw, (goat_width, goat_height))
        
        surprised_goat_raw = pygame.image.load(
            os.path.join(homepage_assets_dir, 'surprised_goat.png')
        ).convert_alpha()
        self.surprised_goat = pygame.transform.scale(surprised_goat_raw, (goat_width, goat_height))
        
        # Calculate goat target position - comes from bottom, positioned slightly down (lower on screen)
        # Display is 540x380, move goat slightly down (adds small margin from bottom edge)
        goat_margin_right = 10  # Margin from right edge
        goat_offset_down = 6  # Small offset to move goat slightly down in visible area
        self.goat_target_pos = [
            self.display.get_width() - goat_width - goat_margin_right,  # Right edge with margin
            self.display.get_height() - goat_height + goat_offset_down  # Slightly down (lower Y = down on screen)
        ]
        # Set initial goat position to start from bottom center (below screen)
        self.goat_pos = [
            self.goat_target_pos[0],  # Same x position as target (starts from bottom center horizontally)
            self.display.get_height()  # Below screen (will move up to target)
        ]
        
        # Load speech bubble and scale it down
        speech_bubble_raw = pygame.image.load(
            os.path.join(homepage_assets_dir, 'speech_bubble.png')
        ).convert_alpha()
        # Scale speech bubble to slightly smaller size
        bubble_scale = 0.18
        bubble_width = int(speech_bubble_raw.get_width() * bubble_scale)
        bubble_height = int(speech_bubble_raw.get_height() * bubble_scale)
        self.speech_bubble = pygame.transform.scale(speech_bubble_raw, (bubble_width, bubble_height))
        
        # Initialize pixel font using PressStart2P font
        font_path = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
        self.font = pygame.font.Font(font_path, 8)  # Smaller font for buttons to fit within button
        # Title font size - reduced to fit longer text
        self.title_font = pygame.font.Font(font_path, 14)  # Smaller font to fit longer title
        
        # Animation state
        self.elapsed_time = 0.0
        self.phase = "typing"  # "typing", "goat_entrance", "goat_surprised", "speech_bubble", "idle"
        
        # Title text and typing animation (split into 3 lines to fit on screen)
        self.title_lines = [
            "The Time I Was Reincarnated As A",
            "Teleporting Goat In A 2D",
            "Puzzle Platformer"
        ]
        # Track each letter's animation state: (char, line_index, char_index_in_line, appear_time, hop_progress)
        self.letter_animations = []  # List of tuples: (char, line_idx, char_idx, appear_time, hop_progress)
        self.typing_speed = 0.035  # seconds between each letter appearing (faster)
        self.last_letter_time = 0.0
        self.current_line_idx = 0  # Current line being animated
        self.current_char_idx = 0  # Current character index in current line
        self.title_finished = False
        self.hop_duration = 0.25  # Duration of hop animation in seconds (faster)
        self.hop_height = 10  # Maximum height of hop in pixels
        self.title_x = 20  # Left-aligned position (margin from edge)
        self.title_y = 60  # Top position for first line (added margin at top)
        
        # Goat animation state (position is set after goat is loaded, above)
        self.goat_entrance_speed = 80.0  # pixels per second
        self.goat_entrance_start_time = 0.0
        self.goat_entrance_duration = 0.0
        self.goat_is_visible = False
        self.goat_surprised = False
        self.goat_surprised_start_time = 0.0
        
        # Speech bubble
        self.speech_bubble_visible = False
        self.speech_bubble_start_time = 0.0
        
        # Button states
        self.show_start_button = True
        self.show_menu_buttons = False  # Select Level, Generate Level
        
        # Loading state
        self.is_loading = False
        self.loading_text = "Generating level..."
        
        # Button definitions (rectangles) - Start button positioned below title, left-aligned
        # Calculate based on title height: 3 lines of text + spacing
        title_line_height = 20  # Line spacing matches the rendering (20px)
        self.start_button_y = self.title_y + (len(self.title_lines) * title_line_height) + 15  # Below title with more spacing
        # Smaller button size with rounded corners (will be drawn with border_radius)
        button_width = 140
        button_height = 28
        self.start_button_rect = pygame.Rect(self.title_x, self.start_button_y, button_width, button_height)
        # Select Level and Generate Level buttons appear in the same spot as Start Game button
        self.select_level_button_rect = pygame.Rect(self.title_x, self.start_button_y, button_width, button_height)
        self.generate_level_button_rect = pygame.Rect(self.title_x, self.start_button_y, button_width, button_height)
        
        # Animation timing (in seconds) - faster overall
        self.GOAT_ENTRANCE_DELAY = 0.7  # Delay after title finishes before goat enters (faster)
        self.GOAT_SURPRISED_DELAY = 1.0  # Delay after goat reaches position before switching sprite (faster)
        self.SPEECH_BUBBLE_DELAY = 0.3  # Delay after goat becomes surprised before speech bubble appears (faster)
        
    def update(self, dt):
        """Update animation state based on delta time"""
        self.elapsed_time += dt
        
        # Phase 1: Letter hopping animation
        if self.phase == "typing" and not self.title_finished:
            # Spawn letters one by one with hop animation, line by line
            if self.current_line_idx < len(self.title_lines):
                current_line = self.title_lines[self.current_line_idx]
                if self.current_char_idx < len(current_line):
                    if self.elapsed_time - self.last_letter_time >= self.typing_speed:
                        char = current_line[self.current_char_idx]
                        # Add letter animation (char, line_idx, char_idx, appear_time, hop_progress)
                        self.letter_animations.append((char, self.current_line_idx, self.current_char_idx, self.elapsed_time, 0.0))
                        
                        self.current_char_idx += 1
                        self.last_letter_time = self.elapsed_time
                else:
                    # Move to next line
                    self.current_line_idx += 1
                    self.current_char_idx = 0
            else:
                # All lines done, wait for animations to finish
                pass
            
            # Update hop animations for all visible letters
            updated_animations = []
            for char, line_idx, char_idx, appear_time, _ in self.letter_animations:
                time_since_appear = self.elapsed_time - appear_time
                if time_since_appear < self.hop_duration:
                    # Calculate hop progress (bounce up then down)
                    hop_progress = time_since_appear / self.hop_duration
                    if hop_progress < 0.5:
                        # Going up
                        hop_progress = hop_progress * 2  # 0 to 1
                    else:
                        # Coming down
                        hop_progress = 1 - ((hop_progress - 0.5) * 2)  # 1 to 0
                    updated_animations.append((char, line_idx, char_idx, appear_time, hop_progress))
                else:
                    # Animation finished, set progress to 0 (normal position)
                    updated_animations.append((char, line_idx, char_idx, appear_time, 0.0))
            self.letter_animations = updated_animations
            
            # Check if all letters have appeared and animations finished
            if self.current_line_idx >= len(self.title_lines):
                # Wait for all hop animations to finish before moving to next phase
                if all(hop_progress == 0.0 or (self.elapsed_time - appear_time) >= self.hop_duration 
                       for _, _, _, appear_time, hop_progress in self.letter_animations):
                    self.title_finished = True
                    self.phase = "goat_entrance"
                    self.goat_entrance_start_time = self.elapsed_time + self.GOAT_ENTRANCE_DELAY
        
        # Phase 2: Goat entrance (after delay)
        if self.phase == "goat_entrance":
            if self.elapsed_time >= self.goat_entrance_start_time:
                if not self.goat_is_visible:
                    self.goat_is_visible = True
                
                # Calculate progress (0 to 1) - 1.5 seconds for entrance (faster)
                entrance_elapsed = self.elapsed_time - self.goat_entrance_start_time
                entrance_progress = min(entrance_elapsed / 1.5, 1.0)
                
                if entrance_progress >= 1.0:
                    # Goat reached position
                    self.goat_pos = self.goat_target_pos.copy()
                    self.phase = "goat_surprised"
                    self.goat_surprised_start_time = self.elapsed_time + self.GOAT_SURPRISED_DELAY
                else:
                    # Linear interpolation from bottom (below screen) to target position
                    # Goat comes from bottom and moves up to target (x stays same, y moves up)
                    start_y = self.display.get_height()  # Start below screen
                    self.goat_pos[0] = self.goat_target_pos[0]  # X position stays constant
                    self.goat_pos[1] = start_y + (self.goat_target_pos[1] - start_y) * entrance_progress
        
        # Phase 3: Goat becomes surprised
        if self.phase == "goat_surprised":
            if self.elapsed_time >= self.goat_surprised_start_time:
                self.goat_surprised = True
                self.phase = "speech_bubble"
                self.speech_bubble_start_time = self.elapsed_time + self.SPEECH_BUBBLE_DELAY
        
        # Phase 4: Speech bubble appears
        if self.phase == "speech_bubble":
            if self.elapsed_time >= self.speech_bubble_start_time:
                self.speech_bubble_visible = True
                self.phase = "idle"
    
    def render(self):
        """Render all visuals to the pixel canvas"""
        # Clear display
        self.display.fill((0, 0, 0))
        
        # Draw background
        self.display.blit(self.background, (0, 0))
        
        # Draw title text with letter hopping animation - each letter appears with a hop
        # Organize letters by line for proper rendering
        lines_letters = {}  # {line_idx: [(char, char_idx, hop_progress), ...]}
        
        for char, line_idx, char_idx, _, hop_progress in self.letter_animations:
            if line_idx not in lines_letters:
                lines_letters[line_idx] = []
            lines_letters[line_idx].append((char, char_idx, hop_progress))
        
        # Render each line
        for line_idx in sorted(lines_letters.keys()):
            line_letters = sorted(lines_letters[line_idx], key=lambda x: x[1])  # Sort by char_idx
            
            # Calculate base Y position for this line (adjusted spacing for smaller font)
            line_y = self.title_y + (line_idx * 20)
            current_x = self.title_x
            
            # Render each letter individually with hop offset
            for char, char_idx, hop_progress in line_letters:
                # Calculate hop offset (negative Y means up)
                hop_offset_y = -int(hop_progress * self.hop_height)
                
                # Render individual letter
                letter_surface = self.title_font.render(char, False, (0, 0, 0))
                letter_y = line_y + hop_offset_y
                self.display.blit(letter_surface, (current_x, letter_y))
                
                # Move x position for next letter
                current_x += letter_surface.get_width()
        
        # Draw goat (if visible)
        if self.goat_is_visible:
            current_goat_sprite = self.surprised_goat if self.goat_surprised else self.shocked_goat
            self.display.blit(current_goat_sprite, (int(self.goat_pos[0]), int(self.goat_pos[1])))
        
        # Draw speech bubble (if visible)
        if self.speech_bubble_visible and self.goat_is_visible:
            # Position speech bubble at top-left of goat image (slightly to the left)
            bubble_x = int(self.goat_pos[0]) - 110  # More to the left of goat
            bubble_y = int(self.goat_pos[1]) - self.speech_bubble.get_height() - 8  # Above goat
            
            # Clamp bubble position to ensure it's fully visible
            bubble_x = max(5, min(bubble_x, self.display.get_width() - self.speech_bubble.get_width() - 5))
            bubble_y = max(5, bubble_y)  # Ensure it's not off the top of the screen
            
            self.display.blit(self.speech_bubble, (bubble_x, bubble_y))
        
        # Helper function to draw rounded rectangle button
        def draw_rounded_button(rect, text):
            # Draw rounded rectangle button (using border_radius parameter in pygame 2.0+)
            border_radius = 5
            pygame.draw.rect(self.display, (0, 0, 0), rect, border_radius=border_radius)
            # Less bold white border (width 1 instead of 2)
            pygame.draw.rect(self.display, (255, 255, 255), rect, 1, border_radius=border_radius)
            # White text (no antialiasing for pixelated look)
            button_text = self.font.render(text, False, (255, 255, 255))
            text_x = rect.centerx - button_text.get_width() // 2
            text_y = rect.centery - button_text.get_height() // 2
            self.display.blit(button_text, (text_x, text_y))
        
        # Draw Start Game button
        if self.show_start_button:
            draw_rounded_button(self.start_button_rect, "Start Game")
        
        # Draw menu buttons (Select Level, Generate Level) - appear in same spot as Start Game
        if self.show_menu_buttons:
            # Select Level button (same position as Start Game)
            draw_rounded_button(self.select_level_button_rect, "Select Level")
            
            # Generate Level button (appears below Select Level, vertically stacked)
            # Calculate position below Select Level button
            generate_rect = pygame.Rect(
                self.select_level_button_rect.x,
                self.select_level_button_rect.y + self.select_level_button_rect.height + 5,
                self.select_level_button_rect.width,
                self.select_level_button_rect.height
            )
            draw_rounded_button(generate_rect, "Generate Level")
            # Update the stored rect for click detection
            self.generate_level_button_rect = generate_rect
        
        # Draw loading overlay if loading
        if self.is_loading:
            # Semi-transparent dark overlay
            overlay = pygame.Surface(self.display.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.display.blit(overlay, (0, 0))
            
            # Loading text
            loading_surface = self.font.render(self.loading_text, False, (255, 255, 255))
            loading_x = self.display.get_width() // 2 - loading_surface.get_width() // 2
            loading_y = self.display.get_height() // 2 - loading_surface.get_height() // 2
            self.display.blit(loading_surface, (loading_x, loading_y))
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks, return choice string or None"""
        # Ignore clicks while loading
        if self.is_loading:
            return None
        
        # Convert screen coordinates to display coordinates
        display_x = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        display_y = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        display_pos = (display_x, display_y)
        
        # Check Start Game button
        if self.show_start_button and self.start_button_rect.collidepoint(display_pos):
            self.show_start_button = False
            self.show_menu_buttons = True
            return None  # Don't exit yet, show menu buttons
        
        # Check Select Level button
        if self.show_menu_buttons and self.select_level_button_rect.collidepoint(display_pos):
            return "SELECT_LEVEL"
        
        # Check Generate Level button
        if self.show_menu_buttons and self.generate_level_button_rect.collidepoint(display_pos):
            # Return a special value to trigger generation with loading screen in the main loop
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
        # The client gets the API key from the environment variable `GEMINI_API_KEY`.
        client = genai.Client()
        
        # Construct the prompt
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

**EXAMPLE PUZZLE IDEAS:**
- Player must portal to a high platform to get a key, then portal back down to the door
- Player must push a crate through a portal to hold down a pressure plate
- Player must navigate around noportalzones to find valid portal placement spots
- Player must use momentum from falling to launch through a portal

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
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt
        )
        
        # Extract the text response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            # Remove first and last line (markdown fences)
            response_text = '\n'.join(lines[1:-1])
        
        # Remove leading/trailing whitespace
        response_text = response_text.strip()
        
        # Save to data/maps directory
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
    running = True
    
    while running:
        # Calculate delta time
        dt = homepage.clock.tick(60) / 1000.0  # Convert to seconds
        
        # Update animations
        homepage.update(dt)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    choice = homepage.handle_click(event.pos)
                    if choice == "GENERATE_LEVEL_START":
                        # Set loading state and show loading screen
                        homepage.is_loading = True
                        
                        # Render and show loading screen
                        homepage.render()
                        scaled_display = pygame.transform.scale(homepage.display, homepage.screen.get_size())
                        homepage.screen.blit(scaled_display, (0, 0))
                        pygame.display.update()
                        
                        # Generate level (this will block while showing loading screen)
                        generated_path = generate_level_with_gemini()
                        
                        # Clear loading state
                        homepage.is_loading = False
                        
                        if generated_path:
                            # Return GENERATE_LEVEL - caller should load the generated file
                            return "GENERATE_LEVEL"
                        else:
                            # Generation failed, continue loop to stay on homepage
                            print("Failed to generate level. Please check your GEMINI_API_KEY environment variable.")
                            continue
                    elif choice:
                        # User made a choice, exit loop
                        return choice
        
        # Render
        homepage.render()
        
        # Scale pixel canvas to screen size (maintaining pixelated look)
        scaled_display = pygame.transform.scale(homepage.display, homepage.screen.get_size())
        homepage.screen.blit(scaled_display, (0, 0))
        pygame.display.update()
    
    return "QUIT"


# Temporary: This file is runnable separately right now for testing
# TODO: Integrate this with game.py - call run_homepage() from game.py's main entry point
#       and handle the returned choice string to load appropriate game state
if __name__ == "__main__":
    choice = run_homepage()
    print(f"Homepage returned: {choice}")
