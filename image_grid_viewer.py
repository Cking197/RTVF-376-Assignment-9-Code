import yaml
import os
import subprocess

# Configurable grid size
GRID_ROWS = 6
GRID_COLS = 6
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
CONFIG_PATH = "dungeon_window_config.yaml"

# Load config
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)
window_configs = config['windows']

# Create grid mapping
image_grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
for win in window_configs:
    row, col = win['position']
    image_grid[row][col] = win['title']

# Function to open image windows in grid
def open_image_windows():
    cell_width = SCREEN_WIDTH // GRID_COLS
    cell_height = SCREEN_HEIGHT // GRID_ROWS
    python_exe = 'python'  # Use your environment's python if needed
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            img_path = "images/"+image_grid[row][col] if image_grid[row][col] else None
            print(f"Checking for image at: {img_path}")  # Debug print
            if img_path and img_path.lower().endswith('.png') and os.path.exists(img_path):
                x = col * cell_width
                y = row * cell_height
                cmd = [python_exe, "image_viewer_single.py", img_path, str(x), str(y), str(cell_width), str(cell_height)]
                subprocess.Popen(cmd)
    print("Image windows opened in grid. Script will now exit.")


if __name__ == "__main__":
    open_image_windows()
