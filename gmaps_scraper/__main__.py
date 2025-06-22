import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

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
    parser = argparse.ArgumentParser(description='Scrape dental clinics data from Google Maps')
    parser.add_argument('--config', type=str, default='config/locations.json',
                        help='Path to locations config file')
    parser.add_argument('--city', type=str, help='Specific city to scrape')
    parser.add_argument('--district', type=str, help='Specific district to scrape')
    parser.add_argument('--search-term', type=str, help='Specific search term to use')
    parser.add_argument('--radius', type=int, default=25000,
                        help='Search radius in meters (max 50000)')
    parser.add_argument('--output-dir', type=str, default='data',
                        help='Directory to save output data')
    parser.add_argument('--skip-city-search', action='store_true',
                        help='Skip city-level search and only search districts')
    parser.add_argument('--batch-size', type=int, default=20,
                        help='Number of places to process before saving a batch')
    parser.add_argument('--use-grid-search', action='store_true',
                        help='Use grid search method for more comprehensive results')
    parser.add_argument('--grid-width', type=float, default=5.0,
                        help='Width of grid search area in km (default: 5.0)')
    parser.add_argument('--grid-height', type=float, default=5.0,
                        help='Height of grid search area in km (default: 5.0)')
    parser.add_argument('--grid-radius', type=int, default=800,
                        help='Search radius in meters for each grid point (default: 800)')
    return parser.parse_args()


def main():
    """Main function to run the scraper"""
    args = parse_args()

    # Check for API key
    if not API_KEY:
        logger.error("API key not found. Please set GOOGLE_MAPS_API_KEY in your .env file.")
        sys.exit(1)
    else:
        logger.info(f"Using API key: {API_KEY[:5]}...{API_KEY[-5:]}")

    # Create output directory
    output_dir = create_data_directory(args.output_dir)

    # Load locations data
    locations_data = load_json_file(args.config)

    # Initialize scraper, processor and storage
    scraper = GooglePlacesScraper()
    scraper.batch_size = args.batch_size  # Set custom batch size
    processor = DataProcessor()
    storage = get_storage()

    # Determine search terms
    search_terms = [args.search_term] if args.search_term else SEARCH_TERMS

    # Track total places found
    total_places = 0
    all_processed_places = []

    # Create timestamp for run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for city_data in locations_data['cities']:
        city_name = city_data['name']

        # Skip if specific city is provided but doesn't match
        if args.city and args.city.lower() != city_name.lower():
            continue

        logger.info(f"Processing city: {city_name}")

        # First, search at city level (if not skipped)
        if not args.skip_city_search:
            for search_term in search_terms:
                logger.info(f"Searching for '{search_term}' in {city_name}")

                try:
                    if args.use_grid_search:
                        logger.info(f"Using grid search for city {city_name}")
                        places = grid_search_places(
                            scraper,
                            search_term,
                            (city_data['lat'], city_data['lng']),
                            area_width_km=args.grid_width,
                            area_height_km=args.grid_height,
                            search_radius_meters=args.grid_radius,
                            storage=storage,
                            processor=processor,
                            city=city_name
                        )
                    else:
                        places = scraper.fetch_places_with_details(
                            search_term,
                            (city_data['lat'], city_data['lng']),
                            radius=args.radius,
                            storage=storage,
                            processor=processor,
                            search_term=search_term,
                            city=city_name
                        )

                    if places:
                        processed_places = processor.process_places_data(
                            places, search_term=search_term, city=city_name
                        )

                        # Save places for this search
                        if processed_places:
                            all_processed_places.extend(processed_places)

                            # Save final results for this search term
                            filename = f"dental_clinics_{city_name.lower().replace(' ', '_')}_{search_term.replace(' ', '_')}_{timestamp}.json"
                            storage.save(processed_places, filename=filename)

                            total_places += len(processed_places)
                            logger.info(f"Found {len(processed_places)} places for '{search_term}' in {city_name}")

                except Exception as e:
                    logger.error(f"Error processing '{search_term}' for {city_name}: {str(e)}")

                # Delay between search terms
                time.sleep(REQUEST_DELAY)
        else:
            logger.info(f"Skipping city-level search for {city_name} as requested")

        # Then, search at district level if there are districts
        if 'districts' in city_data and city_data['districts']:
            for district in city_data['districts']:
                district_name = district['name']

                # Skip if specific district is provided but doesn't match
                if args.district and args.district.lower() != district_name.lower():
                    continue

                logger.info(f"Processing district: {district_name} in {city_name}")

                for search_term in search_terms:
                    logger.info(f"Searching for '{search_term}' in {district_name}, {city_name}")

                    try:
                        if args.use_grid_search:
                            logger.info(f"Using grid search for district {district_name}")
                            places = grid_search_places(
                                scraper,
                                search_term,
                                (district['lat'], district['lng']),
                                area_width_km=args.grid_width,
                                area_height_km=args.grid_height,
                                search_radius_meters=args.grid_radius,
                                storage=storage,
                                processor=processor,
                                city=city_name,
                                district=district_name
                            )
                        else:
                            places = scraper.fetch_places_with_details(
                                f"{search_term} {district_name}",
                                (district['lat'], district['lng']),
                                radius=min(10000, args.radius),  # Smaller radius for districts
                                storage=storage,
                                processor=processor,
                                search_term=search_term,
                                city=city_name,
                                district=district_name
                            )

                        if places:
                            processed_places = processor.process_places_data(
                                places, search_term=search_term, city=city_name, district=district_name
                            )

                            # Save places for this search
                            if processed_places:
                                all_processed_places.extend(processed_places)

                                # Save final results for this search term and district
                                filename = f"dental_clinics_{city_name.lower().replace(' ', '_')}_{district_name.lower().replace(' ', '_')}_{search_term.replace(' ', '_')}_{timestamp}.json"
                                storage.save(processed_places, filename=filename)

                                total_places += len(processed_places)
                                logger.info(
                                    f"Found {len(processed_places)} places for '{search_term}' in {district_name}, {city_name}")

                    except Exception as e:
                        logger.error(f"Error processing '{search_term}' for {district_name}, {city_name}: {str(e)}")

                    # Delay between search terms
                    time.sleep(REQUEST_DELAY)

    # Save all processed places to a single file
    if all_processed_places:
        filename = f"all_dental_clinics_{timestamp}.json"
        storage.save(all_processed_places, filename=filename)

    logger.info(f"Scraping completed. Total places found: {total_places}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)