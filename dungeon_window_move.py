import pygetwindow as gw
import keyboard
import yaml
import time
import random
import subprocess
import sys
import os
import argparse
import threading
import ctypes

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
GAME_EXTRA_HEIGHT = max(1, cell_height // 3)
GAME_HEIGHT = cell_height + GAME_EXTRA_HEIGHT
GAME_EXTRA_WIDTH = 24
GAME_WIDTH = cell_width + GAME_EXTRA_WIDTH
# Compensate for window frame/asymmetric borders that make centering look left-shifted.
GAME_X_VISUAL_OFFSET = GAME_EXTRA_WIDTH // 2
MOVE_DURATION_SECONDS = 0.5
MOVE_FPS = 60
FOCUS_LOOP_DELAY_SECONDS = 0.05
TILE_WINDOW_DISCOVERY_RETRIES = 12
TILE_WINDOW_DISCOVERY_DELAY_SECONDS = 0.05

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
MAP_TILE_SET = set(map_tiles)
game_started = False
game_fullscreen = False

user32 = ctypes.windll.user32
SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
VK_MENU = 0x12
KEYEVENTF_KEYUP = 0x0002


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


def minimize_all_tile_windows():
    """Minimize every configured tile window if it is open."""
    for win_cfg in window_configs:
        title = win_cfg['title']
        matches = gw.getWindowsWithTitle(title)
        if not matches:
            continue
        try:
            matches[0].minimize()
        except Exception as e:
            print(f"Could not minimize tile window '{title}': {e}")


def ensure_tile_window(row, col):
    """Get or launch the tile window for a grid position."""
    title = grid[row][col]
    if not title:
        return None

    matches = gw.getWindowsWithTitle(title)
    if matches:
        return matches[0]

    img_path = os.path.join("images", title)
    if not (img_path.lower().endswith('.png') and os.path.exists(img_path)):
        return None

    x = col * cell_width
    y = row * cell_height
    python_exe = sys.executable
    try:
        proc = subprocess.Popen([
            python_exe,
            "image_viewer_single.py",
            img_path,
            str(x),
            str(y),
            str(cell_width),
            str(cell_height)
        ])
        tile_processes.append(proc)
    except Exception as e:
        print(f"Could not launch tile window '{title}': {e}")
        return None

    # Give the spawned viewer a brief moment to register its window title.
    for _ in range(TILE_WINDOW_DISCOVERY_RETRIES):
        time.sleep(TILE_WINDOW_DISCOVERY_DELAY_SECONDS)
        matches = gw.getWindowsWithTitle(title)
        if matches:
            return matches[0]
    return None


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


def force_foreground_window(win):
    """Use Win32 calls to bring a window to front and request foreground focus."""
    hwnd = getattr(win, "_hWnd", None)
    if not hwnd:
        return

    try:
        # Restore first if minimized/hidden.
        user32.ShowWindow(hwnd, SW_RESTORE)

        # Brief topmost pulse helps raise z-order above other app windows.
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

        # ALT key unlock trick: Windows often permits SetForegroundWindow right after ALT input.
        user32.keybd_event(VK_MENU, 0, 0, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

        # Retry focus requests a few times because foreground changes are timing-sensitive.
        for _ in range(5):
            fg_hwnd = user32.GetForegroundWindow()
            current_tid = user32.GetCurrentThreadId()
            fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)

            if fg_tid and fg_tid != current_tid:
                user32.AttachThreadInput(fg_tid, current_tid, True)
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.SetActiveWindow(hwnd)
                user32.AttachThreadInput(fg_tid, current_tid, False)
            else:
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.SetActiveWindow(hwnd)

            if user32.GetForegroundWindow() == hwnd:
                break
            time.sleep(0.02)
    except Exception:
        pass


def move_game_to_pos(animate=False, force=False):
    """Move the game window to overlap the current grid cell."""
    if game_fullscreen and not force:
        keep_game_on_top()
        return

    win = get_game_window()
    if not win:
        print(f"Game window '{game_title}' not found!")
        return

    # Grid cell origin for the player's current tile.
    cell_x = player_pos[1] * cell_width
    cell_y = player_pos[0] * cell_height

    try:
        if win.isMinimized:
            win.restore()
        win.resizeTo(GAME_WIDTH, GAME_HEIGHT)

        # Some apps clamp/adjust window size; center using the actual resulting size.
        actual_w = win.width
        actual_h = win.height
        x = cell_x + ((cell_width - actual_w) // 2) + GAME_X_VISUAL_OFFSET
        y = cell_y + ((cell_height - actual_h) // 2)
        x = max(0, min(x, SCREEN_WIDTH - actual_w))
        y = max(0, min(y, SCREEN_HEIGHT - actual_h))

        if animate:
            start_x, start_y = win.left, win.top
            steps = max(1, int(MOVE_DURATION_SECONDS * MOVE_FPS))
            sleep_per_step = MOVE_DURATION_SECONDS / steps
            for step in range(1, steps + 1):
                t = step / steps
                nx = round(start_x + (x - start_x) * t)
                ny = round(start_y + (y - start_y) * t)
                win.moveTo(nx, ny)
                force_foreground_window(win)
                time.sleep(sleep_per_step)
        else:
            win.moveTo(x, y)

            # Some windows finalize frame/client size after the first move.
            # Recenter once more so initial placement (including P start) is exact.
            actual_w = win.width
            actual_h = win.height
            recenter_x = cell_x + ((cell_width - actual_w) // 2) + GAME_X_VISUAL_OFFSET
            recenter_y = cell_y + ((cell_height - actual_h) // 2)
            recenter_x = max(0, min(recenter_x, SCREEN_WIDTH - actual_w))
            recenter_y = max(0, min(recenter_y, SCREEN_HEIGHT - actual_h))
            win.moveTo(recenter_x, recenter_y)

        win.activate()
    except Exception as e:
        print(f"Could not move game window: {e}")


def keep_game_on_top():
    """Ensure the game window is restored and focused above other windows."""
    win = get_game_window()
    if not win:
        return
    try:
        if win.isMinimized:
            win.restore()
        force_foreground_window(win)
        win.activate()
    except Exception:
        # Windows focus rules may occasionally block activation; retry loop handles this.
        pass


def focus_enforcer_loop():
    """Continuously try to keep the game window active while the script runs."""
    while True:
        keep_game_on_top()
        time.sleep(FOCUS_LOOP_DELAY_SECONDS)


def open_tile_at(row, col):
    """Restore the tile window at a specific grid location, launching it if needed."""
    title = grid[row][col]
    if not title:
        return
    tile_win = ensure_tile_window(row, col)
    if not tile_win:
        return
    try:
        if tile_win.isMinimized:
            tile_win.restore()
    except Exception as e:
        print(f"Could not open tile window '{title}': {e}")


def start_game_window():
    """Start state transition: place the game window at its configured position."""
    global game_started
    if game_started:
        return
    game_started = True
    move_game_to_pos()
    keep_game_on_top()
    print("Game started: window positioned.")


def move_player(direction):
    if not game_started:
        print("Press P to start first.")
        keep_game_on_top()
        return
    deltas = {
        'up': (-1, 0),
        'down': (1, 0),
        'left': (0, -1),
        'right': (0, 1)
    }
    if direction not in deltas:
        keep_game_on_top()
        return

    prev_row, prev_col = player_pos
    dr, dc = deltas[direction]
    next_row = prev_row + dr
    next_col = prev_col + dc
    if not (0 <= next_row < GRID_ROWS and 0 <= next_col < GRID_COLS):
        keep_game_on_top()
        return

    player_pos[0] = next_row
    player_pos[1] = next_col

    print(f"Player moved to: {player_pos}")
    move_game_to_pos(animate=True)
    open_tile_at(prev_row, prev_col)
    keep_game_on_top()


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
                    if (col, row) not in MAP_TILE_SET:
                        win_objs[title].minimize()
                except Exception as e:
                    print(f"Could not move/resize window '{title}': {e}")
    # Place game window on top at current position
    move_game_to_pos()
    keep_game_on_top()
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
    keep_game_on_top()



def toggle_map():
    """One-way map reveal: open all map tiles that are currently minimized."""
    win = get_game_window()
    if not win:
        return
    opened_count = 0
    
    for col, row in map_tiles:
        if not grid[row][col]:
            continue
        tile_win = ensure_tile_window(row, col)
        if not tile_win:
            continue
        try:
            if tile_win.isMinimized:
                tile_win.restore()
                opened_count += 1
        except Exception as e:
            print(f"Could not open tile window at ({row}, {col}): {e}")
    keep_game_on_top()
    print(f"Map reveal complete. Opened {opened_count} tile(s).")


def toggle_fullscreen_game():
    """Toggle the game window between fullscreen and normal grid-managed position."""
    global game_fullscreen

    win = get_game_window()
    if not win:
        print(f"Game window '{game_title}' not found!")
        return

    try:
        if win.isMinimized:
            win.restore()

        if not game_fullscreen:
            win.moveTo(0, 0)
            win.resizeTo(SCREEN_WIDTH, SCREEN_HEIGHT)
            game_fullscreen = True
            print("Game window fullscreen enabled.")
        else:
            game_fullscreen = False
            move_game_to_pos(force=True)
            print("Game window returned to normal position.")

        keep_game_on_top()
    except Exception as e:
        print(f"Could not toggle fullscreen: {e}")



keyboard.add_hotkey('w', lambda: move_player('up'))
keyboard.add_hotkey('s', lambda: move_player('down'))
keyboard.add_hotkey('a', lambda: move_player('left'))
keyboard.add_hotkey('d', lambda: move_player('right'))
keyboard.add_hotkey('ctrl+l', layout_windows)
keyboard.add_hotkey('k', lambda: screenshake(3))
keyboard.add_hotkey('m', toggle_map)
keyboard.add_hotkey('b', toggle_fullscreen_game)
keyboard.add_hotkey('p', start_game_window)
keyboard.add_hotkey('0', close_all_and_exit)

threading.Thread(target=focus_enforcer_loop, daemon=True).start()

print(f"Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}, Cell: {cell_width}x{cell_height}")
print("Launching all tile windows...")
open_image_windows()
time.sleep(1.0)
minimize_all_tile_windows()
print("All tile windows minimized at startup.")

print(f"Game window: '{game_title}' starting at grid position {player_pos}")
print("Controls: P to place/start game window, W/A/S/D to move, M to reveal map tiles (one-way), B to toggle fullscreen, K to screenshake, CTRL+L to lay out grid, 0 to close all & quit. Press ESC to quit.")

keyboard.wait('esc')
close_all_and_exit()
