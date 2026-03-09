import pygetwindow as gw
import keyboard
import yaml
import time
import random
import subprocess
import sys
import os
import argparse

# Parse command-line arguments for resolution
parser = argparse.ArgumentParser(description="Dungeon window mover")
parser.add_argument('--width', type=int, default=2560, help='Display resolution width (default: 2560)')
parser.add_argument('--height', type=int, default=1440, help='Display resolution height (default: 1440)')
args = parser.parse_args()

# Configurable grid size
GRID_ROWS = 6
GRID_COLS = 6
SCREEN_WIDTH = args.width
SCREEN_HEIGHT = args.height

CONFIG_PATH = "dungeon_window_config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Load game window info
game_config = config['Game']
game_title = game_config['-title']
game_start = game_config['-position']

# Load grid windows
window_configs = config['windows']
grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
for win in window_configs:
    row, col = win['position']
    grid[row][col] = win['title']

# Player position starts at the game window's configured position
player_pos = list(game_start)

cell_width = SCREEN_WIDTH // GRID_COLS
cell_height = SCREEN_HEIGHT // GRID_ROWS

tile_processes = []

# coords that are not black screens
map_tiles = [
    (1,0), (2,0),
    (2,1), (4,1), (5,1),
    (0,2), (1,2), (2,2), (3,2), (4,2),
    (1,3), (2,3), (3,3),
    (2,4),
    (1,5), (2,5), (3,5)
]
# bool for map toggle
#global map_toggled
map_toggled = True


def open_image_windows():
    """Launch all tile image windows in their grid positions."""
    python_exe = sys.executable
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            title = grid[row][col]
            if not title:
                continue
            img_path = os.path.join("images", title)
            if not (img_path.lower().endswith('.png') and os.path.exists(img_path)):
                continue
            x = col * cell_width
            y = row * cell_height
            proc = subprocess.Popen([python_exe, "image_viewer_single.py",
                              img_path, str(x), str(y),
                              str(cell_width), str(cell_height)])
            tile_processes.append(proc)
    print("Image tile windows launched.")


def close_all_and_exit():
    """Close all tile windows and exit."""
    print("Closing all windows...")
    for proc in tile_processes:
        try:
            proc.terminate()
        except Exception:
            pass
    os._exit(0)


def get_game_window():
    matches = gw.getWindowsWithTitle(game_title)
    if matches:
        return matches[0]
    return None


def move_game_to_pos():
    """Move the game window to overlap the current grid cell."""
    win = get_game_window()
    if not win:
        print(f"Game window '{game_title}' not found!")
        return
    x = player_pos[1] * cell_width
    y = player_pos[0] * cell_height
    try:
        win.moveTo(x, y)
        win.resizeTo(cell_width, cell_height)
        win.activate()
    except Exception as e:
        print(f"Could not move game window: {e}")


def move_player(direction):
    row, col = player_pos
    if direction == 'up' and row > 0:
        player_pos[0] -= 1
    elif direction == 'down' and row < GRID_ROWS - 1:
        player_pos[0] += 1
    elif direction == 'left' and col > 0:
        player_pos[1] -= 1
    elif direction == 'right' and col < GRID_COLS - 1:
        player_pos[1] += 1
    print(f"Player moved to: {player_pos}")
    move_game_to_pos()


def layout_windows():
    """Lay out all grid windows in their positions."""
    win_titles = [win['title'] for win in window_configs]
    win_objs = {}
    for title in win_titles:
        matches = gw.getWindowsWithTitle(title)
        if matches:
            win_objs[title] = matches[0]
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            title = grid[row][col]
            if title and title in win_objs:
                x = col * cell_width
                y = row * cell_height
                try:
                    win_objs[title].moveTo(x, y)
                    win_objs[title].resizeTo(cell_width, cell_height)
                    if (col, row) not in map_tiles:
                        win_objs[title].minimize()
                except Exception as e:
                    print(f"Could not move/resize window '{title}': {e}")
    # Place game window on top at current position
    move_game_to_pos()
    print("Windows laid out in grid.")


def screenshake(amt):
    """Screenshake the game window."""
    win = get_game_window()
    if not win:
        return
    x_ref, y_ref = win.left, win.top
    start = time.time()
    while time.time() - start < 0.5:
        dx = random.randint(-amt, amt)
        dy = random.randint(-amt, amt)
        win.moveTo(x_ref + dx, y_ref + dy)
        time.sleep(0.01)
    win.moveTo(x_ref, y_ref)



def toggle_map():
    """Toggles the map to show."""
    ## windows to toggle
    #[1,0] [2,0]
    #[2,1] [4,1] [5,1]
    #[0~4,2]
    #[1~3,3]
    #[2,4]
    #[1~3,5]
    win = get_game_window()
    if not win:
        return
    win.minimize()
    win_titles = [win['title'] for win in window_configs]
    win_objs = {title: gw.getWindowsWithTitle(title)[0] for title in win_titles if gw.getWindowsWithTitle(title)}
    global map_toggled
    
    for col, row in map_tiles:
        t = grid[row][col]
        if t and t in win_objs:
            try:
                if map_toggled:
                    win_objs[t].minimize()
                else:
                    win_objs[t].restore()
            except Exception as e:
                print(f"Could not minimize/restore window '{t}': {e}")
    win.restore()
    map_toggled = not map_toggled
    print("Map toggled")



keyboard.add_hotkey('w', lambda: move_player('up'))
keyboard.add_hotkey('s', lambda: move_player('down'))
keyboard.add_hotkey('a', lambda: move_player('left'))
keyboard.add_hotkey('d', lambda: move_player('right'))
keyboard.add_hotkey('ctrl+l', layout_windows)
keyboard.add_hotkey('k', lambda: screenshake(3))
keyboard.add_hotkey('m', toggle_map)
keyboard.add_hotkey('0', close_all_and_exit)

print(f"Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}, Cell: {cell_width}x{cell_height}")
print("Launching tile windows...")
open_image_windows()
time.sleep(2)  # Give tile windows time to open

print(f"Game window: '{game_title}' starting at grid position {player_pos}")
print("Controls: W/A/S/D to move game window, M to toggle map, K to screenshake, CTRL+L to lay out grid, 0 to close all & quit. Press ESC to quit.")

# Place game window at starting position
move_game_to_pos()

keyboard.wait('esc')
close_all_and_exit()
