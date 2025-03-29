import requests
import time
import json
from urllib.parse import quote
from utils.logger import logger
from config.settings import (
    API_KEY,
    LANGUAGE,
    REGION,
    SEARCH_RADIUS,
    REQUEST_DELAY,
    MAX_RETRIES
)
from utils.helpers import retry_function


class GooglePlacesScraper:
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.batch_size = 20  # Batch size for saving data
        self.places_batch = []  # Store places temporarily

        if not self.api_key:
            raise ValueError("API key is required. Set it in .env file or pass it to the constructor.")

    def _make_request(self, url, params=None):
        """Make a request to the Google Places API."""
        if params is None:
            params = {}

        params['key'] = self.api_key

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Log the raw response for debugging
            logger.debug(f"API Response: {json.dumps(data, ensure_ascii=False)}")
            logger.debug(f"API Response Status: {data.get('status')}")
            logger.debug(f"API Request URL: {response.url}")

            if 'error_message' in data:
                logger.debug(f"API Error Message: {data.get('error_message')}")

            if 'results' in data:
                logger.debug(f"Number of results: {len(data['results'])}")
                if len(data['results']) > 0:
                    logger.debug(f"First result: {json.dumps(data['results'][0], ensure_ascii=False)}")
            else:
                logger.debug("No results returned from API")
            if data.get('status') == 'OK' or data.get('status') == 'ZERO_RESULTS':
                return data
            else:
                error_message = f"API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}"
                logger.error(error_message)
                if data.get('status') == 'OVER_QUERY_LIMIT':
                    logger.warning("API quota exceeded. Waiting longer before retry...")
                    time.sleep(REQUEST_DELAY * 5)  # Wait longer for quota errors
                raise Exception(error_message)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            raise

    def search_places(self, keyword, location, radius=SEARCH_RADIUS, language=LANGUAGE, region=REGION):
        """
        Search for places using the Places API Text Search.

        Args:
            keyword (str): The search term
            location (tuple): Latitude and longitude of the search center
            radius (int): Search radius in meters (max 50000)
            language (str): Language for results
            region (str): Region bias

        Returns:
            list: List of places data
        """
        url = f"{self.base_url}/textsearch/json"

        # Encode keyword for URL
        query = quote(keyword)

        # Format location as "lat,lng"
        location_str = f"{location[0]},{location[1]}"

        params = {
            'query': query,
            'location': location_str,
            'radius': radius,
            'language': language,
            'region': region
        }

        logger.info(f"Searching for '{keyword}' near {location_str} with radius {radius}m")

        all_results = []
        next_page_token = None

        # First request
        response = retry_function(self._make_request, max_retries=MAX_RETRIES)(url, params)

        if response and 'results' in response:
            all_results.extend(response['results'])
            next_page_token = response.get('next_page_token')

        # Get additional pages if available
        page_count = 1
        while next_page_token:
            logger.info(f"Fetching next page (page {page_count + 1}) of results for '{keyword}'")

            # Wait before making the next request (token needs time to become valid)
            time.sleep(REQUEST_DELAY * 2)

            page_params = {'pagetoken': next_page_token,
                           'key': self.api_key}  # Simplified params for pagetoken requests
            try:
                page_url = f"{self.base_url}/textsearch/json"
                page_response = retry_function(self._make_request, max_retries=MAX_RETRIES)(page_url, page_params)

                if page_response and 'results' in page_response:
                    new_results = page_response['results']
                    logger.info(f"Found {len(new_results)} additional results on page {page_count + 1}")
                    all_results.extend(new_results)
                    next_page_token = page_response.get('next_page_token')
                else:
                    logger.warning(f"No results returned for page {page_count + 1}")
                    next_page_token = None
            except Exception as e:
                logger.error(f"Error fetching page {page_count + 1}: {str(e)}")
                next_page_token = None

            page_count += 1

            # Avoid infinite loops
            if page_count >= 3:  # Google typically provides maximum of 3 pages (60 results)
                logger.info(f"Reached maximum page count ({page_count})")
                break

            # Normal delay between requests
            time.sleep(REQUEST_DELAY)

        logger.info(f"Found total of {len(all_results)} results for '{keyword}' across {page_count} page(s)")
        return all_results

    def get_place_details(self, place_id, language=LANGUAGE):
        """
        Get detailed information about a place.

        Args:
            place_id (str): The Place ID
            language (str): Language for results

        Returns:
            dict: Place details
        """
        url = f"{self.base_url}/details/json"

        params = {
            'place_id': place_id,
            'language': language,
            'fields': 'name,place_id,formatted_address,formatted_phone_number,'
                      'geometry,rating,types,website,opening_hours,'
                      'price_level,user_ratings_total'
        }

        logger.info(f"Getting details for place_id: {place_id}")

        response = retry_function(self._make_request, max_retries=MAX_RETRIES)(url, params)

        if response and 'result' in response:
            return response['result']

        return None

    def fetch_places_with_details(self, keyword, location, radius=SEARCH_RADIUS, language=LANGUAGE, region=REGION,
                                  storage=None, processor=None, search_term=None, city=None, district=None):
        """
        Search for places and fetch detailed information for each result.

        Args:
            keyword (str): The search term
            location (tuple): Latitude and longitude of the search center
            radius (int): Search radius in meters (max 50000)
            language (str): Language for results
            region (str): Region bias
            storage: Storage instance to save data
            processor: DataProcessor instance to process data
            search_term: Original search term
            city: City name
            district: District name

        Returns:
            list: List of places with detailed information
        """
        # First, search for places
        search_results = self.search_places(keyword, location, radius, language, region)

        # Then, get details for each place
        detailed_results = []
        batch_count = 0

        # Reset batch for this search
        self.places_batch = []

        for place in search_results:
            place_id = place.get('place_id')
            if place_id:
                # Add delay between requests
                time.sleep(REQUEST_DELAY)

                place_details = self.get_place_details(place_id, language)
                if place_details:
                    detailed_results.append(place_details)

                    # Process and add to batch if processor and storage are provided
                    if processor and storage:
                        processed_place = processor.extract_place_data(place_details, search_term, city, district)
                        if processed_place:
                            self.places_batch.append(processed_place)

                            # Save batch if we've reached batch size
                            batch_count += 1
                            if len(self.places_batch) >= self.batch_size:
                                self._save_batch(storage, search_term, city, district)

        # Save any remaining places in batch
        if processor and storage and self.places_batch:
            self._save_batch(storage, search_term, city, district)

        logger.info(f"Fetched details for {len(detailed_results)} places for keyword '{keyword}'")
        return detailed_results

    def _save_batch(self, storage, search_term=None, city=None, district=None):
        """
        Save current batch of places to storage.

        Args:
            storage: Storage instance
            search_term: Search term used
            city: City name
            district: District name
        """
        if not self.places_batch:
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        batch_size = len(self.places_batch)

        # Create filename
        parts = []
        if city:
            parts.append(city.lower().replace(' ', '_'))
        if district:
            parts.append(district.lower().replace(' ', '_'))
        if search_term:
            parts.append(search_term.replace(' ', '_'))
        parts.append(timestamp)

        filename = f"dental_clinics_{'_'.join(parts)}_batch_{batch_size}.json"

        # Save data
        try:
            storage.save(self.places_batch, filename=filename)
            logger.info(f"Saved batch of {batch_size} places to storage")
            # Reset batch after saving
            self.places_batch = []
        except Exception as e:
            logger.error(f"Error saving batch: {str(e)}")