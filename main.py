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
import pygame
from homepage import run_homepage
from level_select import run_level_select
from game import Game


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
