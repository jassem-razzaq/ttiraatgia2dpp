"""
Main controller for routing between Homepage, Level Selection, and Game screens.

Flow:
- Start at Homepage
- Homepage -> Level Selection (when "Select Level" clicked)
- Level Selection -> Game (when a level is selected)
- Level Selection -> Homepage (when "Back" clicked)
- Game -> Level Selection (when level completed or quit/escape pressed)
"""

import sys
import os
import pygame
from homepage import run_homepage
from level_select import run_level_select
from game import Game


def run_introduction(screen):
    """
    Show the introduction screen with panning animation.
    
    Args:
        screen: pygame screen surface
        
    Returns:
        None (when introduction is skipped or completes)
    """
    game_dir = os.path.dirname(os.path.abspath(__file__))
    intro_image_path = os.path.join(game_dir, 'data', 'images', 'introduction.png')
    
    # Load introduction image
    try:
        intro_image = pygame.image.load(intro_image_path).convert()
    except:
        # If image doesn't exist, skip introduction
        return
    
    # Get screen dimensions
    screen_width, screen_height = screen.get_size()
    
    # Scale image with zoom out (smaller than screen width for black bars)
    image_width = intro_image.get_width()
    image_height = intro_image.get_height()
    zoom_factor = 0.75  # Zoom out to 75% (adjust this value to change zoom level)
    scaled_width = int(screen_width * zoom_factor)
    scale_factor = scaled_width / image_width
    scaled_height = int(image_height * scale_factor)
    
    intro_image = pygame.transform.scale(intro_image, (scaled_width, scaled_height))
    
    # Calculate horizontal offset to center the image (creates black bars on sides)
    x_offset = (screen_width - scaled_width) // 2
    
    # Load font for skip text
    font_path = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
    try:
        skip_font = pygame.font.Font(font_path, 8)
    except:
        skip_font = pygame.font.Font(None, 16)
    
    skip_text = skip_font.render("(press any button to skip)", False, (255, 255, 255))
    skip_text_padding = 10
    skip_text_x = screen_width - skip_text.get_width() - skip_text_padding
    skip_text_y = screen_height - skip_text.get_height() - skip_text_padding
    
    # Panning animation variables
    scroll_y = 0  # Start at top of image
    pan_speed = 0.35  # Pixels per frame to scroll down
    clock = pygame.time.Clock()
    
    # If image is shorter than screen height, no panning needed
    if scaled_height <= screen_height:
        # Just display the image centered
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)  # Exit game entirely on close button
                if event.type == pygame.KEYDOWN:
                    return  # Skip on any key press
            
            screen.fill((0, 0, 0))
            y_offset = (screen_height - scaled_height) // 2
            screen.blit(intro_image, (x_offset, y_offset))
            # Draw skip text in bottom right
            screen.blit(skip_text, (skip_text_x, skip_text_y))
            pygame.display.update()
            clock.tick(60)
    else:
        # Pan down through the image
        max_scroll = scaled_height - screen_height
        
        while scroll_y < max_scroll:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)  # Exit game entirely on close button
                if event.type == pygame.KEYDOWN:
                    return  # Skip on any key press
            
            # Clear screen
            screen.fill((0, 0, 0))
            
            # Draw the portion of the image at current scroll position, centered horizontally
            screen.blit(intro_image, (x_offset, -scroll_y))
            # Draw skip text in bottom right
            screen.blit(skip_text, (skip_text_x, skip_text_y))
            
            pygame.display.update()
            
            # Update scroll position
            scroll_y += pan_speed
            clock.tick(60)
        
        # Once panning completes, wait for key press or timeout
        wait_start = pygame.time.get_ticks()
        wait_duration = 2000  # Wait 2 seconds at the end before auto-advancing
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)  # Exit game entirely on close button
                if event.type == pygame.KEYDOWN:
                    return  # Skip on any key press
            
            # Auto-advance after wait duration
            if pygame.time.get_ticks() - wait_start >= wait_duration:
                return
            
            # Keep displaying the bottom of the image, centered horizontally
            screen.fill((0, 0, 0))
            screen.blit(intro_image, (x_offset, -max_scroll))
            # Draw skip text in bottom right
            screen.blit(skip_text, (skip_text_x, skip_text_y))
            pygame.display.update()
            clock.tick(60)

def fade_transition(screen=None, duration=0.25, fade_out=True):
    """
    Perform a fade transition on the screen.
    
    Args:
        screen: pygame screen surface (if None, uses display.get_surface())
        duration: Duration of fade in seconds
        fade_out: True for fade out (to black), False for fade in (from black)
    
    Returns:
        None
    """
    if screen is None:
        screen = pygame.display.get_surface()
    
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    
    while True:
        # Handle events to prevent window freezing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # Let main loop handle QUIT
        
        clock.tick(60)
        elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
        progress = min(elapsed / duration, 1.0)
        
        # Calculate alpha: 0 (transparent) to 255 (opaque)
        if fade_out:
            # Fade out: 0 -> 255
            alpha = int(progress * 255)
        else:
            # Fade in: 255 -> 0
            alpha = int((1.0 - progress) * 255)
        
        # Create black overlay
        overlay = pygame.Surface(screen.get_size())
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.update()
        
        if progress >= 1.0:
            break

def run_game(level_path):
    """
    Run the game with a specific level.
    
    Args:
        level_path: Path to the level JSON file
    
    Returns:
        str: "BACK_TO_SELECT" when game should return to level selection, "QUIT" to quit
    """
    game = Game(level_path=level_path)
    return game.run()

def main():
    """Main game loop - routes between different screens"""
    # Initialize pygame display once
    pygame.init()
    
    # Set up screen (matching homepage/game dimensions)
    screen = pygame.display.set_mode((960, 640))
    pygame.display.set_caption('Portal Puzzle')
    
    # Show introduction screen first (only on first run)
    run_introduction(screen)
    
    while True:
        # Start at homepage
        choice = run_homepage()
        
        if choice == "QUIT":
            break
        elif choice == "SELECT_LEVEL":
            # Fade out from homepage
            fade_transition(duration=0.25, fade_out=True)
            
            # Go to level selection (it will render immediately)
            while True:
                level_choice = run_level_select()
                
                if level_choice == "QUIT":
                    sys.exit(0)
                elif level_choice == "BACK":
                    # Fade out from level select
                    fade_transition(duration=0.25, fade_out=True)
                    # Return to homepage (will fade in automatically on first render)
                    break
                else:
                    # Fade out from level select
                    fade_transition(duration=0.25, fade_out=True)
                    
                    # level_choice is a level path - run the game
                    game_result = run_game(level_choice)
                    
                    # Restore cursor visibility after game (game hides it)
                    pygame.mouse.set_visible(True)
                    
                    # Fade in to level select after game
                    fade_transition(duration=0.25, fade_out=False)
                    
                    if game_result == "QUIT":
                        sys.exit(0)
                    # If game_result is "BACK_TO_SELECT", loop back to level selection
                    # (already in the level selection loop)
            
            # Fade in to homepage after returning from level select
            fade_transition(duration=0.25, fade_out=False)
        elif choice == "GENERATE_LEVEL":
            # Fade out from homepage
            fade_transition(duration=0.25, fade_out=True)
            
            # Run the generated level (it's always at generated_level.json)
            import os
            game_dir = os.path.dirname(os.path.abspath(__file__))
            generated_path = os.path.join(game_dir, 'data', 'maps', 'generated_level.json')
            game_result = run_game(generated_path)
            
            # Restore cursor visibility after game (game hides it)
            pygame.mouse.set_visible(True)
            
            # Fade in to homepage after game
            fade_transition(duration=0.25, fade_out=False)
            
            if game_result == "QUIT":
                sys.exit(0)
            # After generated level, return to homepage
            # (loop back to start)

if __name__ == "__main__":
    main()
