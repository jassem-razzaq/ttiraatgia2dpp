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
    while True:
        # Start at homepage
        choice = run_homepage()
        
        if choice == "QUIT":
            break
        elif choice == "SELECT_LEVEL":
            # Go to level selection
            while True:
                level_choice = run_level_select()
                
                if level_choice == "QUIT":
                    sys.exit(0)
                elif level_choice == "BACK":
                    # Return to homepage
                    break
                else:
                    # level_choice is a level path - run the game
                    game_result = run_game(level_choice)
                    
                    # Restore cursor visibility after game (game hides it)
                    pygame.mouse.set_visible(True)
                    
                    if game_result == "QUIT":
                        sys.exit(0)
                    # If game_result is "BACK_TO_SELECT", loop back to level selection
                    # (already in the level selection loop)
        elif choice == "GENERATE_LEVEL":
            # Run the generated level (it's always at generated_level.json)
            import os
            game_dir = os.path.dirname(os.path.abspath(__file__))
            generated_path = os.path.join(game_dir, 'data', 'maps', 'generated_level.json')
            game_result = run_game(generated_path)
            
            # Restore cursor visibility after game (game hides it)
            pygame.mouse.set_visible(True)
            
            if game_result == "QUIT":
                sys.exit(0)
            # After generated level, return to homepage
            # (loop back to start)

if __name__ == "__main__":
    main()
