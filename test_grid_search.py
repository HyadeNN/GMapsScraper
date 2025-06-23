import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from config.settings import SEARCH_TERMS, REQUEST_DELAY, API_KEY
from utils.logger import logger
from utils.helpers import load_json_file, create_data_directory
from utils.grid_search import grid_search_places
from core.scraper import GooglePlacesScraper
from core.data_processor import DataProcessor
from core.storage import get_storage


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Grid search for dental clinics')
    parser.add_argument('--config', type=str, default='gmaps_scraper/config/locations.json',
                        help='Path to locations config file')
    parser.add_argument('--city', type=str, default='İstanbul',
                        help='City to search (default: İstanbul)')
    parser.add_argument('--district', type=str, default='Kadıköy',
                        help='District to search (default: Kadıköy)')
    parser.add_argument('--search-term', type=str,
                        help='Specific search term to use (default: first term from settings)')
    parser.add_argument('--output-dir', type=str, default='data/grid_search',
                        help='Directory to save output data (default: data/grid_search)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Batch size for intermediate saves (default: 10)')
    parser.add_argument('--width', type=float, default=5.0,
                        help='Width of search area in km (default: 5.0)')
    parser.add_argument('--height', type=float, default=5.0,
                        help='Height of search area in km (default: 5.0)')
    parser.add_argument('--radius', type=int, default=800,
                        help='Search radius in meters for each point (default: 800)')
    return parser.parse_args()


def find_location(locations_data, city_name, district_name):
    """Find location coordinates for the specified city and district"""
    for city in locations_data['cities']:
        if city['name'].lower() == city_name.lower():
            if district_name:
                for district in city.get('districts', []):
                    if district['name'].lower() == district_name.lower():
                        return {
                            'city': city['name'],
                            'district': district['name'],
                            'lat': district['lat'],
                            'lng': district['lng']
                        }
            # Return city coordinates if district not specified or not found
            return {
                'city': city['name'],
                'district': None,
                'lat': city['lat'],
                'lng': city['lng']
            }
    return None


def main():
    """Main function to run the grid search"""
    args = parse_args()

    # Check for API key
    if not API_KEY:
        logger.error("API key not found. Please set GOOGLE_MAPS_API_KEY in your .env file.")
        sys.exit(1)
    else:
        logger.info(f"Using API key: {API_KEY[:5]}...{API_KEY[-5:]}")

    # Create output directory
    output_dir = create_data_directory(args.output_dir)
    logger.info(f"Saving results to {output_dir}")

    # Load locations data
    locations_data = load_json_file(args.config)

    # Find location data for the specified city and district
    location = find_location(locations_data, args.city, args.district)
    if not location:
        logger.error(f"City '{args.city}' or district '{args.district}' not found in config.")
        sys.exit(1)

    # Initialize scraper, processor and storage
    scraper = GooglePlacesScraper()
    scraper.batch_size = args.batch_size
    processor = DataProcessor()
    storage = get_storage()

    # Determine search term
    search_term = args.search_term if args.search_term else SEARCH_TERMS[0]
    logger.info(f"Using search term: {search_term}")

    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Starting grid search for {location['city']}, "
                f"{location['district'] if location['district'] else 'all districts'}")
    logger.info(f"Search area: {args.width}km x {args.height}km, radius per point: {args.radius}m")

    # Prepare location coords
    center_coords = (location['lat'], location['lng'])

    try:
        # Perform grid search
        all_places = grid_search_places(
            scraper,
            search_term,
            center_coords,
            area_width_km=args.width,
            area_height_km=args.height,
            search_radius_meters=args.radius,
            storage=storage,
            processor=processor,
            city=location['city'],
            district=location['district']
        )

        # Process all places (this is needed to get the final processed format)
        processed_places = processor.process_places_data(
            all_places,
            search_term=search_term,
            city=location['city'],
            district=location['district']
        )

        # Save final results
        if processed_places:
            city_str = location['city'].lower().replace(' ', '_')
            district_str = f"_{location['district'].lower().replace(' ', '_')}" if location['district'] else ""
            search_str = search_term.replace(' ', '_')

            filename = f"grid_search_{city_str}{district_str}_{search_str}_{timestamp}_complete.json"
            file_path = storage.save(processed_places, filename=filename)

            logger.info(f"Found total of {len(processed_places)} unique places")
            logger.info(f"Final complete results saved to {file_path}")
        else:
            logger.warning("No places were found after processing.")

    except Exception as e:
        logger.error(f"Error during grid search: {str(e)}", exc_info=True)
        sys.exit(1)

    logger.info("Grid search completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)