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
    
    # Load and play intro music
    intro_music_path = os.path.join(game_dir, 'data', 'audio', 'intro_music.mp3')
    try:
        if os.path.exists(intro_music_path):
            pygame.mixer.music.load(intro_music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # Loop the music
            music_playing = True
        else:
            music_playing = False
    except:
        music_playing = False
    
    # Load introduction image
    try:
        intro_image = pygame.image.load(intro_image_path).convert()
    except:
        # If image doesn't exist, skip introduction and stop music
        if music_playing:
            pygame.mixer.music.stop()
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
    # Start from a negative position to show black space at the top initially
    initial_offset = 150  # Pixels of black space to show at the top before image appears
    scroll_y = -initial_offset  # Start above the image (negative = shows black at top)
    pan_speed = 0.5  # Pixels per frame to scroll down
    clock = pygame.time.Clock()
    initial_music_volume = 0.5  # Starting music volume
    
    # If image is shorter than screen height, no panning needed
    if scaled_height <= screen_height:
        # Just display the image centered
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if music_playing:
                        pygame.mixer.music.stop()
                    sys.exit(0)  # Exit game entirely on close button
                if event.type == pygame.KEYDOWN:
                    if music_playing:
                        pygame.mixer.music.stop()
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
        # Add bottom_offset to show black space at the bottom at the end
        bottom_offset = 150  # Pixels of black space to show at the bottom after image ends
        scroll_end_point = scaled_height - screen_height + bottom_offset  # Point where 150px black space is shown
        fade_duration = 2  # Duration of fade in seconds
        fade_started = False
        fade_start_time = 0
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if music_playing:
                        pygame.mixer.music.stop()
                    sys.exit(0)  # Exit game entirely on close button
                if event.type == pygame.KEYDOWN:
                    if music_playing:
                        pygame.mixer.music.stop()
                    return  # Skip on any key press
            
            # Clear screen
            screen.fill((0, 0, 0))
            
            # Draw the portion of the image at current scroll position, centered horizontally
            screen.blit(intro_image, (x_offset, -scroll_y))
            # Draw skip text in bottom right
            screen.blit(skip_text, (skip_text_x, skip_text_y))
            
            # Start fade when we reach the 150px bottom offset point
            if scroll_y >= scroll_end_point and not fade_started:
                fade_started = True
                fade_start_time = pygame.time.get_ticks()
            
            # Apply fade overlay if fade has started
            fade_alpha = 0
            if fade_started:
                elapsed = (pygame.time.get_ticks() - fade_start_time) / 1000.0
                progress = min(elapsed / fade_duration, 1.0)
                fade_alpha = int(progress * 255)
                
                # Fade out music along with the visual fade
                if music_playing:
                    # Music volume fades from initial_volume to 0
                    music_volume = initial_music_volume * (1.0 - progress)
                    pygame.mixer.music.set_volume(music_volume)
                
                if fade_alpha > 0:
                    fade_overlay = pygame.Surface(screen.get_size())
                    fade_overlay.fill((0, 0, 0))
                    fade_overlay.set_alpha(fade_alpha)
                    screen.blit(fade_overlay, (0, 0))
                
                # Once fade completes (completely black), stop music and go to homepage
                if progress >= 1.0:
                    if music_playing:
                        pygame.mixer.music.stop()
                    return  # Goes to homepage
            
            pygame.display.update()
            
            # Continue scrolling even during fade
            scroll_y += pan_speed
            
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
            # Stop menu music when quitting
            pygame.mixer.music.stop()
            break
        elif choice == "SELECT_LEVEL":
            # Fade out from homepage (keep music playing - it continues in level selection)
            fade_transition(duration=0.25, fade_out=True)
            
            # Go to level selection (it will render immediately)
            while True:
                level_choice = run_level_select()
                
                if level_choice == "QUIT":
                    # Stop menu music when quitting
                    pygame.mixer.music.stop()
                    sys.exit(0)
                elif level_choice == "BACK":
                    # Fade out from level select (keep music playing - returns to homepage)
                    fade_transition(duration=0.25, fade_out=True)
                    # Return to homepage (will fade in automatically on first render)
                    break
                else:
                    # Stop menu music when starting a game
                    pygame.mixer.music.stop()
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
            # Stop menu music when starting generated level
            pygame.mixer.music.stop()
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
