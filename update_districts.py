import os
import sys
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir
sys.path.append(str(project_root))

# Import and run the UI
from utils.district_updater_ui import DistrictUpdaterApp
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = DistrictUpdaterApp(root)
    root.mainloop()