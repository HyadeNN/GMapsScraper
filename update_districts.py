#!/usr/bin/env python3
"""
District Updater with GUI
Fixes XCB/X11 threading issues for Linux systems
"""

import os
import sys
from pathlib import Path

# Fix for XCB/X11 threading issues - must be set before importing tkinter
os.environ['QT_X11_NO_MITSHM'] = '1'
os.environ['_X11_NO_MITSHM'] = '1'
os.environ['XDG_SESSION_TYPE'] = 'x11'

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir
sys.path.append(str(project_root))

def check_display():
    """Check if display is available"""
    if 'DISPLAY' not in os.environ:
        print("Warning: No DISPLAY environment variable found")
        return False
    return True

def main():
    """Main function with better error handling"""
    
    # Check display availability
    if not check_display():
        print("GUI cannot start without a display. Try using update_districts_cli.py instead.")
        return
    
    try:
        # Import tkinter modules
        import tkinter as tk
        from gmaps_scraper.utils.district_updater_ui import DistrictUpdaterApp
        
        # Create root window with additional safety
        root = tk.Tk()
        
        # Set additional X11 properties
        try:
            root.tk.call('tk', 'scaling', 1.0)  # Set DPI scaling
        except:
            pass
            
        # Initialize app
        app = DistrictUpdaterApp(root)
        
        # Start GUI
        print("Starting District Updater GUI...")
        root.mainloop()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install tkinter: sudo apt-get install python3-tk")
        return
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        print("\nXCB/X11 Error detected. Possible solutions:")
        print("1. Try: export DISPLAY=:0")
        print("2. Try: xhost +local:")
        print("3. Use CLI version: python update_districts_cli.py file.xlsx")
        return

if __name__ == "__main__":
    main()