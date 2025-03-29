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
from core.scraper import GooglePlacesScraper
from core.data_processor import DataProcessor
from core.storage import get_storage


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test scraper for a single district')
    parser.add_argument('--config', type=str, default='config/locations.json',
                        help='Path to locations config file')
    parser.add_argument('--city', type=str, default='İstanbul',
                        help='City to test (default: İstanbul)')
    parser.add_argument('--district', type=str, default='Kadıköy',
                        help='District to test (default: Kadıköy)')
    parser.add_argument('--search-term', type=str,
                        help='Specific search term to use (default: first term from settings)')
    parser.add_argument('--radius', type=int, default=2000,
                        help='Search radius in meters (default: 5000)')
    parser.add_argument('--output-dir', type=str, default='data/test',
                        help='Directory to save output data (default: data/test)')
    parser.add_argument('--batch-size', type=int, default=5,
                        help='Batch size for intermediate saves (default: 5)')
    parser.add_argument('--verify-location', action='store_true',
                        help='Verify that results are in the specified district')
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
    """Test function to run the scraper for a single district"""
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
    scraper.batch_size = args.batch_size  # Set custom batch size
    processor = DataProcessor()
    storage = get_storage()

    # Determine search term
    search_term = args.search_term if args.search_term else SEARCH_TERMS[0]
    logger.info(f"Using search term: {search_term}")

    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Starting test scrape for {location['city']}, "
                f"{location['district'] if location['district'] else 'all districts'}")
    logger.info(f"Using search radius of {args.radius} meters")

    # Prepare location coords
    coords = (location['lat'], location['lng'])

    # Create search queries that ensure we find places in the target district
    # We'll use both direct district name and search term combinations
    search_queries = []

    # If we have a district, make it prominent in the search query
    if location['district']:
        # Primary search with district name first for better localization
        search_queries.append(f"{location['district']} {search_term}")
        # Secondary search with term first (may give different results)
        search_queries.append(f"{search_term} {location['district']}")
    else:
        search_queries.append(search_term)

    all_places = []
    all_processed_places = []

    # Try multiple search queries to maximize results
    for query in search_queries:
        logger.info(f"Searching for '{query}' at coordinates {coords}")

        try:
            # Use search_places directly to handle pagination properly
            raw_places = scraper.search_places(
                query,
                coords,
                radius=args.radius
            )

            logger.info(f"Found {len(raw_places)} places in search results for '{query}'")

            if raw_places:
                # Process each place to get details
                place_details_list = []
                batch_count = 0
                current_batch = []

                for raw_place in raw_places:
                    place_id = raw_place.get('place_id')
                    if place_id:
                        # Add delay between requests
                        time.sleep(REQUEST_DELAY)

                        # Get details for this place
                        place_details = scraper.get_place_details(place_id)
                        if place_details:
                            # Add to our overall list
                            place_details_list.append(place_details)

                            # Process this place
                            processed_place = processor.extract_place_data(
                                place_details,
                                search_term=search_term,
                                city=location['city'],
                                district=location['district']
                            )

                            # Only add if we have a valid processed place
                            if processed_place:
                                # If verifying location, check for district match
                                address = processed_place.get('location', {}).get('address', '').lower()
                                district_present = (
                                        not args.verify_location or
                                        (location['district'] and location['district'].lower() in address)
                                )

                                if district_present:
                                    current_batch.append(processed_place)
                                    all_processed_places.append(processed_place)

                                    # Save batch if we've reached batch size
                                    batch_count += 1
                                    if len(current_batch) >= args.batch_size:
                                        batch_filename = f"dental_clinics_{location['city'].lower().replace(' ', '_')}_{location['district'].lower().replace(' ', '_') if location['district'] else ''}_{search_term.replace(' ', '_')}_{timestamp}_batch_{len(current_batch)}.json"
                                        storage.save(current_batch, filename=batch_filename)
                                        logger.info(f"Saved batch of {len(current_batch)} places to storage")
                                        current_batch = []

                # Save any remaining places in the batch
                if current_batch:
                    batch_filename = f"dental_clinics_{location['city'].lower().replace(' ', '_')}_{location['district'].lower().replace(' ', '_') if location['district'] else ''}_{search_term.replace(' ', '_')}_{timestamp}_batch_{len(current_batch)}.json"
                    storage.save(current_batch, filename=batch_filename)
                    logger.info(f"Saved final batch of {len(current_batch)} places to storage")

                # Add these places to our overall list
                all_places.extend(place_details_list)

                logger.info(f"Processed {len(all_processed_places)} places for query '{query}'")
            else:
                logger.warning(f"No places found in search results for '{query}'")

        except Exception as e:
            logger.error(f"Error during search for '{query}': {str(e)}", exc_info=True)

    # Save all processed places to a final results file
    if all_processed_places:
        city_str = location['city'].lower().replace(' ', '_')
        district_str = f"_{location['district'].lower().replace(' ', '_')}" if location['district'] else ""
        search_str = search_term.replace(' ', '_')

        filename = f"test_dental_clinics{city_str}{district_str}_{search_str}_{timestamp}_complete.json"
        file_path = storage.save(all_processed_places, filename=filename)

        logger.info(f"Found total of {len(all_processed_places)} unique places across all searches")
        logger.info(f"Final complete results saved to {file_path}")
    else:
        logger.warning("No places were found after processing.")

    logger.info("Test scrape completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)