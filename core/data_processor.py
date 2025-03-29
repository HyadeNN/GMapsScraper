from datetime import datetime
from utils.logger import logger


class DataProcessor:
    def __init__(self):
        self.processed_places = set()

    def extract_place_data(self, place_data, search_term=None, city=None, district=None):
        """
        Extract and structure relevant data from a Google Places API response.
        """
        if not place_data:
            return None

        place_id = place_data.get('place_id')

        # Skip if already processed
        if place_id in self.processed_places:
            return None

        self.processed_places.add(place_id)

        processed_data = {
            'id': place_id,
            'name': place_data.get('name', ''),
            'types': place_data.get('types', []),
            'contact': {
                'phone': place_data.get('formatted_phone_number', ''),
                'website': place_data.get('website', '')
            },
            'location': {
                'address': place_data.get('formatted_address', ''),
                'city': city or self._extract_city_from_address(place_data.get('formatted_address', '')),
                'district': district or self._extract_district_from_address(place_data.get('formatted_address', '')),
                'postal_code': self._extract_postal_code(place_data.get('formatted_address', '')),
                'latitude': place_data.get('geometry', {}).get('location', {}).get('lat'),
                'longitude': place_data.get('geometry', {}).get('location', {}).get('lng')
            },
            'details': {
                'rating': place_data.get('rating'),
                'user_ratings_total': place_data.get('user_ratings_total'),
                'price_level': place_data.get('price_level'),
                'opening_hours': self._format_opening_hours(place_data.get('opening_hours', {}))
            },
            'metadata': {
                'retrieved_at': datetime.now().isoformat(),
                'search_term': search_term
            }
        }

        return processed_data

    def _extract_city_from_address(self, address):
        """
        Extract city name from address string.
        This is a simple implementation and might need refinement.
        """
        if not address:
            return ''

        parts = address.split(',')
        if len(parts) >= 2:
            # Usually city is in the second-to-last part in Turkish addresses
            return parts[-2].strip()
        return ''

    def _extract_district_from_address(self, address):
        """
        Extract district name from address string.
        This is a simple implementation and might need refinement.
        """
        if not address:
            return ''

        parts = address.split(',')
        if len(parts) >= 3:
            # Usually district is in the third-to-last part in Turkish addresses
            return parts[-3].strip()
        return ''

    def _extract_postal_code(self, address):
        """
        Extract postal code from address string.
        """
        if not address:
            return ''

        import re
        # Turkish postal codes are 5 digits
        postal_code_match = re.search(r'\b\d{5}\b', address)
        if postal_code_match:
            return postal_code_match.group(0)
        return ''

    def _format_opening_hours(self, opening_hours):
        """
        Format opening hours into a structured format.
        """
        if not opening_hours or 'periods' not in opening_hours:
            return {}

        days_map = {
            0: 'sunday',
            1: 'monday',
            2: 'tuesday',
            3: 'wednesday',
            4: 'thursday',
            5: 'friday',
            6: 'saturday'
        }

        formatted_hours = {}

        for period in opening_hours.get('periods', []):
            day = days_map.get(period.get('open', {}).get('day'))
            if not day:
                continue

            open_time = period.get('open', {}).get('time', '')
            close_time = period.get('close', {}).get('time', '')

            if open_time and close_time:
                open_time = f"{open_time[:2]}:{open_time[2:]}"
                close_time = f"{close_time[:2]}:{close_time[2:]}"

                if day not in formatted_hours:
                    formatted_hours[day] = []

                formatted_hours[day].append(f"{open_time}-{close_time}")

        return formatted_hours

    def process_places_data(self, places, search_term=None, city=None, district=None):
        """
        Process a list of place data.
        """
        processed_places = []

        for place in places:
            processed_place = self.extract_place_data(place, search_term, city, district)
            if processed_place:
                processed_places.append(processed_place)

        logger.info(f"Processed {len(processed_places)} places data")
        return processed_places