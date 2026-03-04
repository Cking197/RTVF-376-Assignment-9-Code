import pygetwindow as gw
import keyboard
import yaml
import os


#This script is outdated and needs to be adjusted to match new scripts.

#goals:
#open base map of windows
#open "cover" windows before map
#open "item location" windows from compas (earlier than map, so might require some work on our part
#instead of swapping windows, can just open/move player window on top of other windows
#maybe can even make the player window slide to match the movement between rooms?

# Configurable grid size
grid_rows = 6
grid_cols = 6
screen_width = gw.getWindowsWithTitle(os.path.basename(__file__))[0].width if gw.getWindowsWithTitle(os.path.basename(__file__)) else 1920
screen_height = gw.getWindowsWithTitle(os.path.basename(__file__))[0].height if gw.getWindowsWithTitle(os.path.basename(__file__)) else 1080

def create_grid(rows, cols):
    return [[None for _ in range(cols)] for _ in range(rows)]

grid = create_grid(grid_rows, grid_cols)

config_path = "dungeon_window_config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
window_configs = config['windows']

# Assign windows to grid
for win in window_configs:
    row, col = win['position']
    grid[row][col] = win['title']

# Player position (row, col)
player_pos = [0, 0]

def list_windows():
    windows = gw.getAllTitles()
    return [w for w in windows if w.strip()]

def move_player(direction):
    row, col = player_pos
    if direction == 'up' and row > 0:
        player_pos[0] -= 1
    elif direction == 'down' and row < grid_rows - 1:
        player_pos[0] += 1
    elif direction == 'left' and col > 0:
        player_pos[1] -= 1
    elif direction == 'right' and col < grid_cols - 1:
        player_pos[1] += 1
    print(f"Player moved to: {player_pos}")

def layout_windows():
    # Lay out windows in grid: top->bottom, left->right
    win_titles = [win['title'] for win in window_configs]
    win_objs = {title: gw.getWindowsWithTitle(title)[0] for title in win_titles if gw.getWindowsWithTitle(title)}
    cell_width = screen_width // grid_cols
    cell_height = screen_height // grid_rows
    for row in range(grid_rows):
        for col in range(grid_cols):
            title = grid[row][col]
            if title and title in win_objs:
                x = col * cell_width
                y = row * cell_height
                try:
                    win_objs[title].moveTo(x, y)
                    win_objs[title].resizeTo(cell_width, cell_height)
                except Exception as e:
                    print(f"Could not move/resize window '{title}': {e}")
    print("Windows laid out in grid.")

def swap_windows():
    # Implement window swapping logic here
    print(f"Swapping windows at position: {player_pos}")

keyboard.add_hotkey('w', lambda: move_player('up'))
keyboard.add_hotkey('s', lambda: move_player('down'))
keyboard.add_hotkey('a', lambda: move_player('left'))
keyboard.add_hotkey('d', lambda: move_player('right'))
keyboard.add_hotkey('space', swap_windows)
keyboard.add_hotkey('ctrl+l', layout_windows)

print("Controls: W/A/S/D to move, SPACE to swap windows, CTRL+L to lay out grid. Press ESC to quit.")
print("Available windows:")
for title in list_windows():
    print(f"- {title}")

keyboard.wait('esc')
print("Exiting.")
