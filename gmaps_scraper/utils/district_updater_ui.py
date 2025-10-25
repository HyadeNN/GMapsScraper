import os
import sys

# Fix XCB threading issues before importing tkinter
os.environ['QT_X11_NO_MITSHM'] = '1'
os.environ['_X11_NO_MITSHM'] = '1'

# Try to fix threading issues
import threading
import time

# Now import tkinter with error handling
try:
    import tkinter as tk
    from tkinter import filedialog, ttk, scrolledtext
except ImportError as e:
    print(f"Tkinter import error: {e}")
    print("Please install tkinter: sudo apt-get install python3-tk")
    sys.exit(1)

import pandas as pd
import re
import json
from pathlib import Path


class RedirectText:
    def __init__(self, text_widget, app_instance):
        self.text_widget = text_widget
        self.app_instance = app_instance
        self.buffer = ""

    def write(self, string):
        if self.app_instance and hasattr(self.app_instance, 'safe_print'):
            # Use thread-safe method if available
            self.app_instance.safe_print(string.rstrip())
        else:
            # Fallback to direct write (main thread only)
            try:
                self.buffer += string
                self.text_widget.configure(state="normal")
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
                self.text_widget.configure(state="disabled")
            except tk.TclError:
                # Widget might be destroyed
                pass

    def flush(self):
        pass


class DistrictUpdaterApp:
    def __init__(self, root):
        self.root = root
        
        # Configure root window with thread safety
        try:
            self.root.title("Istanbul District Updater")
            self.root.geometry("700x500")
            self.root.minsize(600, 400)
            
            # Add protocol to handle window closing properly
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Initialize threading lock
            self.thread_lock = threading.Lock()
            
        except Exception as e:
            print(f"Error configuring window: {e}")
            raise

        self.input_file = ""
        self.output_folder = ""

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        # Input file row
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Input Excel File:").pack(side=tk.LEFT, padx=5)
        self.input_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X,
                                                                                expand=True)
        ttk.Button(input_frame, text="Browse...", command=self.browse_input_file).pack(side=tk.LEFT, padx=5)

        # Output folder row
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(output_frame, text="Output Folder:").pack(side=tk.LEFT, padx=5)
        self.output_path_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X,
                                                                                  expand=True)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_folder).pack(side=tk.LEFT, padx=5)

        # Process button
        self.process_button = ttk.Button(file_frame, text="Update Districts", command=self.process_file)
        self.process_button.pack(pady=10)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Redirect stdout to the log widget
        self.stdout_redirect = RedirectText(self.log_text, self)
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout_redirect

    def browse_input_file(self):
        filetypes = [("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Excel File", filetypes=filetypes)
        if filename:
            self.input_file = filename
            self.input_path_var.set(filename)

            # Auto-set output folder to same as input file
            output_dir = os.path.dirname(filename)
            self.output_folder = output_dir
            self.output_path_var.set(output_dir)

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_path_var.set(folder)

    def load_istanbul_districts(self):
        """Load valid Istanbul districts from locations.json"""
        # Find the project root directory and config directory
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent
        config_path = project_root / "config" / "locations.json"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                locations_data = json.load(f)

            # Extract Istanbul districts
            istanbul_data = next((city for city in locations_data['cities'] if city['name'] == 'İstanbul'), None)

            if istanbul_data and 'districts' in istanbul_data:
                return [district['name'] for district in istanbul_data['districts']]

            return []
        except Exception as e:
            print(f"Error loading districts from config: {e}")
            # Fallback list of common Istanbul districts
            return [
                "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler",
                "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü",
                "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt",
                "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane",
                "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer",
                "Şile", "Silivri", "Şişli", "Sultanbeyli", "Sultangazi", "Tuzla",
                "Ümraniye", "Üsküdar", "Zeytinburnu"
            ]

    def extract_district_from_address(self, address, valid_districts):
        """Extract district name from address string."""
        if not address:
            print(f"DEBUG: Empty address")
            return ""

        print(f"DEBUG: Processing address: {address}")

        # Try to find district name in format like "Kadıköy/İstanbul" or "Beşiktaş/Istanbul"
        match = re.search(r'([^,/]+)/(?:İ|I)stanbul', address)
        # Also try to match format like "Beyoğlu/Istanbul, Türkiye"
        if not match:
            match = re.search(r'(\w+)/(İ|I)stanbul', address)
        if match:
            potential_district = match.group(1).strip()
            print(f"DEBUG: Extracted potential district: '{potential_district}'")

            # Check if the extracted district is valid
            for district in valid_districts:
                # Case-insensitive comparison
                if district.lower() == potential_district.lower():
                    print(f"DEBUG: Found exact match: '{district}'")
                    return district  # Return with proper case

            # If not found exactly, look for partial matches
            for district in valid_districts:
                if district.lower() in potential_district.lower():
                    print(f"DEBUG: Found partial match: '{district}' in '{potential_district}'")
                    return district

            print(f"DEBUG: No district match found for '{potential_district}'")
        else:
            print(f"DEBUG: No pattern match in address")

            # Add a more flexible pattern to try
            parts = [part.strip() for part in address.split(',')]
            if len(parts) >= 3:
                district_candidate = parts[-2].strip()
                print(f"DEBUG: Trying alternative extraction: '{district_candidate}'")

                # Check against valid districts
                for district in valid_districts:
                    if district.lower() in district_candidate.lower():
                        print(f"DEBUG: Found match in address part: '{district}'")
                        return district

        return ""

    def update_districts_thread(self):
        try:
            # Get file paths
            input_file = self.input_file
            output_folder = self.output_folder

            if not input_file or not os.path.isfile(input_file):
                print("Error: Please select a valid input Excel file.")
                return

            if not output_folder or not os.path.isdir(output_folder):
                print("Error: Please select a valid output folder.")
                return

            # Generate output file path
            base_filename = os.path.basename(input_file)
            name, ext = os.path.splitext(base_filename)
            output_file = os.path.join(output_folder, f"{name}_updated{ext}")

            print(f"Loading Excel file: {input_file}")

            # Try different engines to ensure we're reading the file properly
            try:
                print("Trying to read Excel with default engine...")
                df = pd.read_excel(input_file)
            except Exception as e:
                print(f"Error with default engine: {str(e)}")
                print("Trying with openpyxl engine...")
                try:
                    df = pd.read_excel(input_file, engine='openpyxl')
                except Exception as e:
                    print(f"Error with openpyxl engine: {str(e)}")
                    print("Trying with xlrd engine...")
                    df = pd.read_excel(input_file, engine='xlrd')

            # Print column names for debugging
            print(f"DEBUG: Available columns: {df.columns.tolist()}")

            # Check if required columns exist
            if 'location_address' not in df.columns:
                print("Error: Required column 'location_address' not found in the Excel file.")
                print("Available columns are:", df.columns.tolist())
                return

            if 'location_district' not in df.columns:
                print("Error: Required column 'location_district' not found in the Excel file.")
                print("Available columns are:", df.columns.tolist())
                return

            # Print a sample of the data
            print("\nDEBUG: Sample data (first 3 rows):")
            print(df.head(3))

            # Load valid districts
            valid_districts = self.load_istanbul_districts()
            print(f"Loaded {len(valid_districts)} valid Istanbul districts:")
            print(", ".join(valid_districts))

            # Start progress bar
            self.root.after(0, self.progress.start)

            # Count initial values
            initial_empty = df['location_district'].isna().sum() + (df['location_district'] == '').sum()

            # Create a backup of the original district column
            df['original_district'] = df['location_district']

            # Update district column
            changes = 0
            print(f"Processing {len(df)} rows...")

            for idx, row in df.iterrows():
                if idx % 100 == 0 and idx > 0:
                    print(f"Processed {idx} rows...")

                address = row['location_address']
                current_district = row['location_district']

                # Get the current district value
                current_district = str(row['location_district']) if not pd.isna(row['location_district']) else ""

                print(f"\nDEBUG: Row {idx} - Current district: '{current_district}'")
                print(f"DEBUG: Row {idx} - Address: '{address}'")

                # First extract the district from the address regardless of current value
                extracted_district = self.extract_district_from_address(address, valid_districts)

                # If we can't extract a valid district, don't update
                if not extracted_district:
                    print(f"DEBUG: Row {idx} - No valid district could be extracted from address")
                    continue

                # Now decide if we need to update based on conditions
                needs_update = False

                if pd.isna(row['location_district']) or current_district == '':
                    print(f"DEBUG: Row {idx} - Current district is empty")
                    needs_update = True
                elif current_district not in valid_districts:
                    print(f"DEBUG: Row {idx} - Current district '{current_district}' not in valid districts list")
                    needs_update = True
                elif extracted_district != current_district:
                    print(
                        f"DEBUG: Row {idx} - Current district '{current_district}' doesn't match extracted '{extracted_district}'")
                    needs_update = True
                else:
                    print(
                        f"DEBUG: Row {idx} - No update needed: Current '{current_district}' matches extracted '{extracted_district}'")

                if needs_update:
                    print(f"DEBUG: Row {idx} - Updating district from '{current_district}' to '{extracted_district}'")
                    df.at[idx, 'location_district'] = extracted_district
                    changes += 1

            # Count final values
            final_empty = df['location_district'].isna().sum() + (df['location_district'] == '').sum()

            # Save updated file
            print(f"Saving updated file to: {output_file}")
            df.to_excel(output_file, index=False)

            print(f"\nUpdate complete!")
            print(f"  - Districts updated: {changes}")
            print(f"  - Empty districts before: {initial_empty}")
            print(f"  - Empty districts after: {final_empty}")
            print(f"Updated file saved to: {output_file}")

            # Suggest manual review
            if final_empty > 0:
                print(f"\nNote: {final_empty} rows still have empty district values.")
                print("Consider manual review of these entries.")

        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            # Stop progress bar and re-enable button
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.process_button.config(state="normal"))

    def process_file(self):
        # Validate inputs
        if not self.input_file or not self.output_folder:
            self.safe_print("Please select both input file and output folder.")
            return
            
        # Disable the button while processing
        self.process_button.config(state="disabled")

        # Clear the log text
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

        # Start the processing in a separate thread
        threading.Thread(target=self.update_districts_thread, daemon=True).start()
    
    def safe_print(self, message):
        """Thread-safe print method"""
        def update_log():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
        
        if threading.current_thread() is threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
    
    def on_closing(self):
        """Handle window closing properly"""
        try:
            # Restore stdout
            if hasattr(self, 'old_stdout'):
                sys.stdout = self.old_stdout
        except:
            pass
        finally:
            self.root.quit()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DistrictUpdaterApp(root)
    root.mainloop()

    # Restore stdout when the app closes
    if hasattr(app, 'old_stdout'):
        sys.stdout = app.old_stdout