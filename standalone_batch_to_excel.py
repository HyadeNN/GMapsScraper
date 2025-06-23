import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Add project root to Python path to access project modules
sys.path.append(str(Path(__file__).parent))

from gmaps_scraper.utils.logger import logger
from gmaps_scraper.utils.helpers import create_data_directory


def flatten_json(nested_json, prefix=''):
    """
    Flatten a nested JSON object into a flat dictionary with key paths
    """
    flat_dict = {}

    for key, value in nested_json.items():
        new_key = f"{prefix}_{key}" if prefix else key

        if isinstance(value, dict):
            flat_dict.update(flatten_json(value, new_key))
        elif isinstance(value, list):
            if all(isinstance(item, dict) for item in value) and value:
                # For lists of dictionaries, use only the first item
                flat_dict.update(flatten_json(value[0], new_key))
            else:
                # For other lists, join as string or keep as is
                flat_dict[new_key] = str(value) if value else ""
        else:
            flat_dict[new_key] = value

    return flat_dict


def main():
    """
    Main function to traverse JSON files and create an Excel file
    """
    # Get the script directory
    script_dir = Path(__file__).parent

    # Get the data directory where JSON files are stored
    data_dir = script_dir / 'data'

    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist!")
        return

    logger.info(f"Looking for JSON files in {data_dir}")

    # Find all JSON files
    json_files = list(data_dir.glob('*.json'))

    if not json_files:
        logger.error("No JSON files found in the data directory")
        return

    logger.info(f"Found {len(json_files)} JSON files")

    # Initialize an empty list to store all records
    all_records = []

    # Initialize set to track unique structure keys
    all_keys = set()

    # Process each JSON file
    for json_file in json_files:
        logger.info(f"Processing {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if the file contains an array of records
            if isinstance(data, list):
                # Process each record
                for record in data:
                    flat_record = flatten_json(record)
                    all_keys.update(flat_record.keys())
                    all_records.append(flat_record)
            elif isinstance(data, dict):
                # Handle case where the file contains a single record
                flat_record = flatten_json(data)
                all_keys.update(flat_record.keys())
                all_records.append(flat_record)

        except Exception as e:
            logger.error(f"Error processing {json_file}: {str(e)}")

    if not all_records:
        logger.error("No valid data found in JSON files")
        return

    logger.info(f"Processed {len(all_records)} records in total")

    # Create DataFrame with all records
    df = pd.DataFrame(all_records)

    # Ensure all columns are present (fill NA for missing keys in some records)
    for key in all_keys:
        if key not in df.columns:
            df[key] = None

    # Create output directory if it doesn't exist
    output_dir = create_data_directory('excel_exports')

    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"dental_clinics_combined_{timestamp}.xlsx"

    # Save to Excel
    df.to_excel(output_file, index=False)

    logger.info(f"Excel file created successfully: {output_file}")
    print(f"Excel file created: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)