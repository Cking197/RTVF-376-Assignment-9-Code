import sys
import tkinter as tk
from PIL import Image, ImageTk
import os

if len(sys.argv) != 6:
    print("Usage: python image_viewer_single.py <image_path> <x> <y> <width> <height>")
    sys.exit(1)

img_path = sys.argv[1]
x = int(sys.argv[2])
y = int(sys.argv[3])
w = int(sys.argv[4])
h = int(sys.argv[5])

if not os.path.exists(img_path):
    print(f"Image not found: {img_path}")
    sys.exit(1)

win = tk.Tk()
win.title(img_path)
win.geometry(f"{w}x{h}+{x}+{y}")
img = Image.open(img_path)
img = img.resize((w, h), Image.Resampling.LANCZOS)
tk_img = ImageTk.PhotoImage(img)
label = tk.Label(win, image=tk_img)
label.image = tk_img
label.pack(fill="both", expand=True)
win.mainloop()
