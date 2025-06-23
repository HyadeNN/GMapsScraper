import math
import itertools
from typing import Tuple, List, Dict

# Handle both direct execution and package imports
try:
    from ..utils.logger import logger
except ImportError:
    from utils.logger import logger


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points
    on the Earth's surface given their latitude and longitude.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (in degrees)
        lat2, lon2: Latitude and longitude of point 2 (in degrees)

    Returns:
        Distance in meters
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r


def calculate_lat_lon_distance(lat: float, lon: float, distance_meters: float,
                               direction: str) -> Tuple[float, float]:
    """
    Calculate a new latitude and longitude given a starting point,
    a distance in meters, and a direction.

    Args:
        lat, lon: Starting latitude and longitude (in degrees)
        distance_meters: Distance to move (in meters)
        direction: One of 'north', 'south', 'east', 'west'

    Returns:
        New latitude and longitude (in degrees)
    """
    # Earth's radius in meters
    R = 6371000

    # Convert latitude and longitude from degrees to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    if direction == 'north':
        # Moving north increases latitude
        new_lat_rad = lat_rad + (distance_meters / R)
        new_lon_rad = lon_rad
    elif direction == 'south':
        # Moving south decreases latitude
        new_lat_rad = lat_rad - (distance_meters / R)
        new_lon_rad = lon_rad
    elif direction == 'east':
        # Moving east increases longitude
        new_lat_rad = lat_rad
        new_lon_rad = lon_rad + (distance_meters / R) / math.cos(lat_rad)
    elif direction == 'west':
        # Moving west decreases longitude
        new_lat_rad = lat_rad
        new_lon_rad = lon_rad - (distance_meters / R) / math.cos(lat_rad)
    else:
        raise ValueError(f"Invalid direction: {direction}")

    # Convert back to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)

    return new_lat, new_lon


def generate_grid_coordinates(center_lat: float, center_lon: float,
                              area_width_km: float, area_height_km: float,
                              search_radius_meters: float = 800) -> List[Tuple[float, float]]:
    """
    Generate a grid of coordinates to cover a rectangular area efficiently with
    circular search areas of specified radius.

    Args:
        center_lat, center_lon: Center of the area (in degrees)
        area_width_km: Width of the area (in kilometers)
        area_height_km: Height of the area (in kilometers)
        search_radius_meters: Radius for each search circle (in meters)

    Returns:
        List of coordinate tuples (latitude, longitude) for search points
    """
    # Convert area dimensions to meters
    area_width_meters = area_width_km * 1000
    area_height_meters = area_height_km * 1000

    # Calculate how far the edges are from the center
    half_width = area_width_meters / 2
    half_height = area_height_meters / 2

    # Get corner coordinates
    north_edge_lat, _ = calculate_lat_lon_distance(center_lat, center_lon, half_height, 'north')
    south_edge_lat, _ = calculate_lat_lon_distance(center_lat, center_lon, half_height, 'south')
    _, east_edge_lon = calculate_lat_lon_distance(center_lat, center_lon, half_width, 'east')
    _, west_edge_lon = calculate_lat_lon_distance(center_lat, center_lon, half_width, 'west')

    # For optimal coverage with minimal overlap, points should be spaced
    # at approximately sqrt(3) * radius distance (hexagonal packing)
    # But for simplicity and to ensure no gaps, we'll use 1.5 * radius
    spacing_factor = 1.5
    distance_between_points = search_radius_meters * spacing_factor

    # Calculate number of points needed in each direction
    num_points_lat = math.ceil(area_height_meters / distance_between_points) + 1
    num_points_lon = math.ceil(area_width_meters / distance_between_points) + 1

    # Generate evenly spaced latitudes and longitudes
    lats = []
    lons = []

    # Latitude steps (north to south)
    lat_step = (north_edge_lat - south_edge_lat) / (num_points_lat - 1) if num_points_lat > 1 else 0
    for i in range(num_points_lat):
        lats.append(north_edge_lat - i * lat_step)

    # Longitude steps (west to east)
    lon_step = (east_edge_lon - west_edge_lon) / (num_points_lon - 1) if num_points_lon > 1 else 0
    for i in range(num_points_lon):
        lons.append(west_edge_lon + i * lon_step)

    # Create a staggered grid pattern for better coverage
    coordinates = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            # Stagger every other row (shift by half the distance)
            offset = (lon_step / 2) if i % 2 else 0
            staggered_lon = lon + offset

            # Only add if within the original boundaries (with some tolerance)
            if west_edge_lon - lon_step / 4 <= staggered_lon <= east_edge_lon + lon_step / 4 and \
                    south_edge_lat - lat_step / 4 <= lat <= north_edge_lat + lat_step / 4:
                coordinates.append((lat, staggered_lon))

    logger.info(f"Generated grid with {len(coordinates)} search points for a "
                f"{area_width_km}km x {area_height_km}km area with {search_radius_meters}m radius")

    return coordinates


def grid_search_places(scraper, search_term, center_coords, area_width_km=5, area_height_km=5,
                       search_radius_meters=800, storage=None, processor=None,
                       city=None, district=None):
    """
    Perform a grid search for places around a center point.

    Args:
        scraper: GooglePlacesScraper instance
        search_term: Term to search for
        center_coords: (latitude, longitude) tuple of center point
        area_width_km: Width of search area in km
        area_height_km: Height of search area in km
        search_radius_meters: Radius for each individual search
        storage: Storage instance (optional)
        processor: DataProcessor instance (optional)
        city: City name (optional)
        district: District name (optional)

    Returns:
        List of all places found
    """
    center_lat, center_lon = center_coords

    # Generate grid coordinates
    grid_coords = generate_grid_coordinates(
        center_lat, center_lon,
        area_width_km, area_height_km,
        search_radius_meters
    )

    # Keep track of place IDs we've seen to avoid duplicates
    seen_place_ids = set()
    all_places = []

    # Perform search at each grid point
    for i, (lat, lon) in enumerate(grid_coords):
        logger.info(f"Searching point {i + 1}/{len(grid_coords)}: ({lat}, {lon})")

        # Search for places
        places = scraper.fetch_places_with_details(
            search_term,
            (lat, lon),
            radius=search_radius_meters,
            storage=storage,
            processor=processor,
            search_term=search_term,
            city=city,
            district=district
        )

        # Filter out duplicates
        new_places = []
        for place in places:
            place_id = place.get('place_id')
            if place_id and place_id not in seen_place_ids:
                seen_place_ids.add(place_id)
                new_places.append(place)

        logger.info(f"Found {len(new_places)} new places at point {i + 1}")
        all_places.extend(new_places)

    logger.info(f"Grid search complete. Found {len(all_places)} unique places in total.")
    return all_places