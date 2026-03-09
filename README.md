# RTVF 376 Assignment 9 Code

Window-grid controller for a Zelda dungeon map workflow.

This project launches image tiles as separate windows, manages their visibility, and moves a game window across a 6x6 grid with keyboard controls.

## Requirements
1. Windows OS.
2. Python 3.10+ recommended.
3. Python standard-library modules used by scripts:
	- `argparse`, `ctypes`, `os`, `random`, `subprocess`, `sys`, `threading`, `time`, `tkinter`
4. Third-party dependencies:

```bash
pip install pygetwindow keyboard pillow pyyaml
```

## Setup (Recommended)
1. Open PowerShell in the project folder.
2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install pygetwindow keyboard pillow pyyaml
```

4. Quick dependency check:

```powershell
python -c "import pygetwindow, keyboard, yaml, PIL, tkinter; print('OK')"
```

If `tkinter` import fails, install/repair Python with `tcl/tk and IDLE` selected.

## Project Files
- `dungeon_window_move.py`: Main runtime script with movement, focus handling, map reveal, and fullscreen toggle.
- `dungeon_window_config.yaml`: Game title, start position, and tile window positions.
- `image_viewer_single.py`: Opens one tile image in a positioned Tk window.
- `images/`: Tile PNG files used by the grid.

## Configuration
Edit `dungeon_window_config.yaml`:
1. Set `Game -> -title` to match the exact game window title.
2. Set `Game -> -position` to the starting grid position as `[row, col]`.
3. Under `windows`, list each tile with:
	- `title`: image filename (for example `row-3-column-4.png`)
	- `position`: `[row, col]` in the 6x6 grid

Notes:
1. Coordinates in Python `map_tiles` are `(col, row)`.
2. Coordinates in YAML `position` are `[row, col]`.

## Run
From this folder:

```bash
python dungeon_window_move.py
```

Optional display override:

```bash
python dungeon_window_move.py --width 2560 --height 1440
```

Helpful utility:

```bash
python window_identifier.py
```

Use it to capture the exact game window title for `dungeon_window_config.yaml`.

## Current Runtime Behavior
1. On launch, tile windows are opened and immediately minimized.
2. Press `P` to place the game window at the configured start tile.
3. Moving with `W/A/S/D` animates movement and restores the tile window from the previous tile.
4. `M` performs one-way map reveal for configured map tiles (opens minimized map tiles; does not hide them again).
5. `B` toggles game window fullscreen on/off.
6. Script continuously attempts to keep the game window active/in front.

## Controls
- `P`: Start/place game window.
- `W`: Move up.
- `A`: Move left.
- `S`: Move down.
- `D`: Move right.
- `M`: Reveal map tiles (one-way).
- `B`: Toggle game fullscreen and return to normal position.
- `K`: Screenshake.
- `Ctrl+L`: Re-layout tile windows to grid.
- `0`: Close all tile windows and exit.
- `Esc`: Quit.
