# The Time I Reincarnated as a Teleporting Goat in a 2D Puzzle Platformer
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)

A teleportation-based puzzle game built with **Python and Pygame**, where a goat travels between gomportals to solve physics based challenges.
Created for **GoatHacks 2026 @ WPI**

### Requirements
- Python 3.9+
- Pygame
- Google Gemini

### Install & Run
1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

2. Install Dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
Create a .env file in the project root and add:
```bash
GOOGLE_GEMINI_KEY=your_api_key_here
```

5. Run the game
```bash
python game.py
```

## Core Idea
You control a goat with a unique teleportation mechanic:
- The goat has a square outline
- Your cursor has a square outline
- When you hold shift, the goat's square locks in place
- The goat can then teleport into the cursor's square
- Releasing Shift restores normal movement
This simple rule unlocks complex puzzles involving positioning, timinig, and spatial reasoning.

## Gameplay Mechanics

### Controls
| Input               | Action                         |
|---------------------|--------------------------------|
| A / D or ← / →      | Move                           |
| W / ↑ / Space       | Jump                           |
| Shift (hold)        | Enter portal mode (red portal) |
| Mouse               | Aim teleport destination       |
| Left Click (with Shift)         | Switch to red portal           |
| Right Click (with Shift)        | Switch to white portal         |
| R                   | Restart level                  |

### Teleportation
- Teleport between the goat and cursor squares
- Preserve relative entry direction to prevent instant re-teleporting
- Portal placement is blocked in restricted zones (`noportalzone` tile)

### Puzzle Elements
- Doors & Keys - Keys are required to unlocked certain paths
- Crates - Can be pushed, teleported, and used as weights
- Springs - Vertical and horizontal launchers
- Anti-portal Zones - Areas where teleporting is disabled

### Level Design
- Tile-based maps loaded from JSON
- Supports off-grid objects (keys, doors, large assets)
- Designed for multi-step spatial puzzles rather than reflex-heavy gameplay


## Credits

Built by Harrison Pham, Jassem Alabdulrazzaq, Bhoomika Gupta, and Tony Hsu Tai<br>
For **GoatHack 2026 @ Worcester Polytechnical Institute**
