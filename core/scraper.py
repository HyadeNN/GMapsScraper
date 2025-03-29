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
            # 'type' parametresi kaldırıldı - Text Search ile uyumlu değil
            # 'fields' parametresi kaldırıldı - Text Search ile uyumlu değil
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
        while next_page_token:
            logger.info(f"Fetching next page of results for '{keyword}'")

            # Wait before making the next request (token needs time to become valid)
            time.sleep(REQUEST_DELAY * 2)

            page_params = {'pagetoken': next_page_token, 'language': language}
            response = retry_function(self._make_request, max_retries=MAX_RETRIES)(url, page_params)

            if response and 'results' in response:
                all_results.extend(response['results'])
                next_page_token = response.get('next_page_token')
            else:
                next_page_token = None

            # Normal delay between requests
            time.sleep(REQUEST_DELAY)

        logger.info(f"Found {len(all_results)} results for '{keyword}'")
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

    def fetch_places_with_details(self, keyword, location, radius=SEARCH_RADIUS, language=LANGUAGE, region=REGION):
        """
        Search for places and fetch detailed information for each result.

        Args:
            keyword (str): The search term
            location (tuple): Latitude and longitude of the search center
            radius (int): Search radius in meters (max 50000)
            language (str): Language for results
            region (str): Region bias

        Returns:
            list: List of places with detailed information
        """
        # First, search for places
        search_results = self.search_places(keyword, location, radius, language, region)

        # Then, get details for each place
        detailed_results = []

        for place in search_results:
            place_id = place.get('place_id')
            if place_id:
                # Add delay between requests
                time.sleep(REQUEST_DELAY)

                place_details = self.get_place_details(place_id, language)
                if place_details:
                    detailed_results.append(place_details)

        logger.info(f"Fetched details for {len(detailed_results)} places for keyword '{keyword}'")
        return detailed_results