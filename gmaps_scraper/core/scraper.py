import requests
import time
import json
from urllib.parse import quote

# Handle both direct execution and package imports
try:
    from ..utils.logger import logger
    from ..config.settings import (
        API_KEY,
        LANGUAGE,
        REGION,
        SEARCH_RADIUS,
        REQUEST_DELAY,
        MAX_RETRIES
    )
    from ..utils.helpers import retry_function
except ImportError:
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
        # Updated to use Places API (New)
        self.base_url = "https://places.googleapis.com/v1/places"
        self.batch_size = 20  # Batch size for saving data
        self.places_batch = []  # Store places temporarily

        if not self.api_key:
            raise ValueError("API key is required. Set it in .env file or pass it to the constructor.")

    def _make_request(self, url, params=None, json_data=None, method='GET'):
        """Make a request to the Google Places API (New)."""
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': '*'  # Will be overridden in specific methods
        }

        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=json_data)
            else:
                response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()
            data = response.json()

            # Log the raw response for debugging
            logger.debug(f"API Response: {json.dumps(data, ensure_ascii=False)}")
            logger.debug(f"API Request URL: {response.url}")

            if 'error' in data:
                logger.debug(f"API Error: {data.get('error')}")
                error_message = f"API Error: {data.get('error', {}).get('message', 'Unknown error')}"
                logger.error(error_message)
                
                # Check for quota errors
                if 'RESOURCE_EXHAUSTED' in str(data.get('error', {})):
                    logger.warning("API quota exceeded. Waiting longer before retry...")
                    time.sleep(REQUEST_DELAY * 5)
                raise Exception(error_message)

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            raise

    def search_places(self, keyword, location, radius=SEARCH_RADIUS, language=LANGUAGE, region=REGION):
        """
        Search for places using the Places API (New) Text Search.

        Args:
            keyword (str): The search term
            location (tuple): Latitude and longitude of the search center
            radius (int): Search radius in meters (max 50000)
            language (str): Language for results
            region (str): Region bias

        Returns:
            list: List of places data
        """
        url = f"{self.base_url}:searchText"
        
        # Pro level fields only (no Enterprise fields like opening_hours)
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.types,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.nationalPhoneNumber,places.websiteUri'
        }

        # Build request body
        request_body = {
            'textQuery': keyword,
            'locationBias': {
                'circle': {
                    'center': {
                        'latitude': location[0],
                        'longitude': location[1]
                    },
                    'radius': radius
                }
            },
            'languageCode': language,
            'regionCode': region.upper(),
            'maxResultCount': 20  # Max 20 per request
        }

        logger.info(f"Searching for '{keyword}' near ({location[0]}, {location[1]}) with radius {radius}m")

        all_results = []
        next_page_token = None

        # First request
        try:
            response = requests.post(url, headers=headers, json=request_body)
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"API Response: {json.dumps(data, ensure_ascii=False)}")
            
            if 'places' in data:
                all_results.extend(data['places'])
                next_page_token = data.get('nextPageToken')
                logger.info(f"Found {len(data['places'])} results in first page")

        except Exception as e:
            logger.error(f"Error in search request: {str(e)}")
            return all_results

        # Get additional pages if available
        page_count = 1
        while next_page_token and page_count < 3:
            logger.info(f"Fetching next page (page {page_count + 1}) of results for '{keyword}'")
            
            # Wait before next request
            time.sleep(REQUEST_DELAY)
            
            # Update request body with page token
            request_body['pageToken'] = next_page_token
            
            try:
                response = requests.post(url, headers=headers, json=request_body)
                response.raise_for_status()
                data = response.json()
                
                if 'places' in data:
                    new_results = data['places']
                    logger.info(f"Found {len(new_results)} additional results on page {page_count + 1}")
                    all_results.extend(new_results)
                    next_page_token = data.get('nextPageToken')
                else:
                    next_page_token = None
                    
            except Exception as e:
                logger.error(f"Error fetching page {page_count + 1}: {str(e)}")
                break
                
            page_count += 1

        logger.info(f"Found total of {len(all_results)} results for '{keyword}' across {page_count} page(s)")
        return all_results

    def get_place_details(self, place_id, language=LANGUAGE):
        """
        Get detailed information about a place using Places API (New).
        Note: In the new API, we already get most details from search, so this might not be needed.

        Args:
            place_id (str): The Place ID
            language (str): Language for results

        Returns:
            dict: Place details
        """
        # In the new API, place details are fetched differently
        # Since we're getting most fields in search, we might not need separate details call
        # But keeping this for compatibility
        
        url = f"{self.base_url}/{place_id}"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'id,displayName,types,formattedAddress,location,rating,userRatingCount,priceLevel,nationalPhoneNumber,websiteUri',
            'Accept-Language': language
        }

        logger.info(f"Getting details for place_id: {place_id}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return data
                
        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")
            
        return None

    def fetch_places_with_details(self, keyword, location, radius=SEARCH_RADIUS, language=LANGUAGE, region=REGION,
                                  storage=None, processor=None, search_term=None, city=None, district=None):
        """
        Search for places using the new API. Since we get most details in search, we don't need separate detail calls.

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
        # Search for places (now includes most details)
        search_results = self.search_places(keyword, location, radius, language, region)

        # With new API, we already have most details from search
        detailed_results = search_results
        batch_count = 0

        # Reset batch for this search
        self.places_batch = []

        for place in search_results:
            # New API uses 'id' instead of 'place_id'
            place_id = place.get('id', '').replace('places/', '') if place.get('id') else None
            
            if place_id:
                # Process and add to batch if processor and storage are provided
                if processor and storage:
                    # Convert new API format to match expected format
                    place_data = self._convert_new_api_format(place)
                    processed_place = processor.extract_place_data(place_data, search_term, city, district)
                    if processed_place:
                        self.places_batch.append(processed_place)

                        # Save batch if we've reached batch size
                        batch_count += 1
                        if len(self.places_batch) >= self.batch_size:
                            self._save_batch(storage, search_term, city, district)

        # Save any remaining places in batch
        if processor and storage and self.places_batch:
            self._save_batch(storage, search_term, city, district)

        logger.info(f"Found and processed {len(detailed_results)} places for keyword '{keyword}'")
        return detailed_results

    def _convert_new_api_format(self, place):
        """
        Convert Places API (New) format to the legacy format expected by data processor.
        """
        # Extract place_id from the new format
        place_id = place.get('id', '').replace('places/', '') if place.get('id') else ''
        
        # Convert location format
        location = place.get('location', {})
        geometry = {
            'location': {
                'lat': location.get('latitude'),
                'lng': location.get('longitude')
            }
        } if location else {}
        
        # Convert displayName to name
        display_name = place.get('displayName', {})
        name = display_name.get('text', '') if isinstance(display_name, dict) else str(display_name)
        
        # Convert new format to legacy format
        converted = {
            'place_id': place_id,
            'name': name,
            'types': place.get('types', []),
            'formatted_address': place.get('formattedAddress', ''),
            'geometry': geometry,
            'rating': place.get('rating'),
            'user_ratings_total': place.get('userRatingCount'),
            'price_level': place.get('priceLevel'),
            'formatted_phone_number': place.get('nationalPhoneNumber', ''),
            'website': place.get('websiteUri', ''),
            # opening_hours removed as it's Enterprise level
        }
        
        return converted

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