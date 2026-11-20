# Doodle Jump Remake

A desktop remake of a vertical platform-jumping game, developed in Python as a programming project.

The application uses **PySide6** for its desktop interface, **Pygame** for gameplay and audio, **SQLite** for persistent game data, and **Matplotlib** for score-history visualization.

## Features

- Interactive platform-jumping gameplay
- Player profiles and persistent scores
- Scoreboard and game-history views
- In-game skins shop
- Adjustable sound and display settings
- Music, sound effects, and custom visual assets

## Requirements

- Python 3.10 or newer (the project contains Python 3.10 bytecode artifacts; other versions have not been tested here)
- Windows, macOS, or Linux with desktop GUI and audio support (compatibility outside the development machine has not been verified)

## Getting started

1. Clone or download this repository.
2. Open a terminal in the folder containing `main.py`.
3. Create a virtual environment:

   **Windows (PowerShell):**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   python main.py
   ```

On first run, the app creates `doodle.db` locally if it does not already exist. Player records and scores are stored there. Settings are read from and written to `data/settings.json`.

## Project structure

```text
main.py                # Application entry point
MainWindow.py          # Main menu and app coordination
GameWindow.py          # Gameplay
Database.py            # SQLite storage
ScoresWindow.py        # Scoreboard
HistoryWindow.py       # History and charts
SkinsWindow.py         # Skins shop
SettingsWindow.py      # Settings
AboutWindow.py         # About dialog
AboutAuthor.py         # Author information
paths.py               # File and resource paths
data/assets/           # Images and sprites
data/sounds/           # Audio assets
data/fonts/            # Application font
data/settings.json     # Initial settings (modified locally during use)
```

## Notes

- `doodle.db` is intentionally excluded from version control because it contains local player and game data.
- `data/settings.json` is included to provide initial settings. Running the game may modify this file; review changes before committing.
- The source code is provided for review and local execution. No standalone executable is required.
- The project includes third-party-style game assets and audio. Their redistribution rights should be checked before making the repository public. No license is granted by this README.