import pygetwindow as gw

print("Open windows and their titles:")
for i, title in enumerate(gw.getAllTitles()):
    if title.strip():
        print(f"{i+1}: '{title}'")

print("\nCopy the exact window titles above into your config file (dungeon_window_config.yaml) to use them in the grid.")
