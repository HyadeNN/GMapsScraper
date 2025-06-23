"""
Location management service.
Handles location data, selection state, and estimation calculations.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from api.models.location import (
    LocationSelection, CityConfig, DistrictConfig, SearchMethod,
    LocationEstimate, PresetSelection, BatchOperation
)


class LocationService:
    """Service for managing location data and selections."""
    
    def __init__(self, locations_file: str = None):
        self.locations_file = Path(locations_file) if locations_file else self._get_default_locations_file()
        self.locations_data = {}
        self.load_locations()
    
    def _get_default_locations_file(self) -> Path:
        """Get the default locations file path."""
        # Try to find locationsV2.json in the gmaps_scraper config directory
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "gmaps_scraper" / "config" / "locationsV2.json",
            Path(__file__).parent.parent / "data" / "locationsV2.json",
            Path(__file__).parent.parent / "config" / "locationsV2.json"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # If none found, return the first one (will be created if needed)
        return possible_paths[0]
    
    def load_locations(self) -> Dict[str, Any]:
        """Load location data from JSON file."""
        if not self.locations_file.exists():
            print(f"Warning: Location file not found: {self.locations_file}")
            return {}
        
        try:
            with open(self.locations_file, 'r', encoding='utf-8') as f:
                self.locations_data = json.load(f)
            
            # Add metadata if not present
            if 'metadata' not in self.locations_data:
                cities_count = len(self.locations_data.get('cities', {}))
                districts_count = sum(
                    len(city_data.get('districts', {})) 
                    for city_data in self.locations_data.get('cities', {}).values()
                )
                
                self.locations_data['metadata'] = {
                    'total_cities': cities_count,
                    'total_districts': districts_count,
                    'last_updated': datetime.now().isoformat(),
                    'source_file': str(self.locations_file)
                }
            
            return self.locations_data
        
        except Exception as e:
            print(f"Error loading locations: {e}")
            return {}
    
    def get_locations_hierarchy(self) -> Dict[str, Any]:
        """Get the complete location hierarchy."""
        return self.locations_data
    
    def get_city_data(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific city."""
        return self.locations_data.get('cities', {}).get(city_name)
    
    def get_district_data(self, city_name: str, district_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific district."""
        city_data = self.get_city_data(city_name)
        if not city_data:
            return None
        return city_data.get('districts', {}).get(district_name)
    
    def search_locations(self, query: str, include_districts: bool = True) -> Dict[str, List[str]]:
        """Search for cities and districts by name."""
        query_lower = query.lower()
        results = {"cities": [], "districts": []}
        
        for city_name, city_data in self.locations_data.get('cities', {}).items():
            # Search cities
            if query_lower in city_name.lower():
                results["cities"].append(city_name)
            
            # Search districts
            if include_districts:
                for district_name in city_data.get('districts', {}):
                    if query_lower in district_name.lower():
                        results["districts"].append(f"{city_name}/{district_name}")
        
        return results
    
    def get_cities_by_region(self, region: str = None) -> List[str]:
        """Get cities filtered by region (if region data is available)."""
        # This would require additional regional data in the JSON
        # For now, return all cities
        return list(self.locations_data.get('cities', {}).keys())
    
    def validate_location_selection(self, selection: LocationSelection) -> Dict[str, Any]:
        """Validate a location selection against available data."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "summary": {
                "valid_cities": 0,
                "invalid_cities": 0,
                "valid_districts": 0,
                "invalid_districts": 0
            }
        }
        
        available_cities = self.locations_data.get('cities', {})
        
        for city_name, city_config in selection.cities.items():
            if city_name not in available_cities:
                validation_result["errors"].append(f"City not found: {city_name}")
                validation_result["summary"]["invalid_cities"] += 1
                validation_result["valid"] = False
                continue
            
            validation_result["summary"]["valid_cities"] += 1
            available_districts = available_cities[city_name].get('districts', {})
            
            for district_name, district_config in city_config.districts.items():
                if district_name not in available_districts:
                    validation_result["errors"].append(f"District not found: {city_name}/{district_name}")
                    validation_result["summary"]["invalid_districts"] += 1
                    validation_result["valid"] = False
                else:
                    validation_result["summary"]["valid_districts"] += 1
        
        return validation_result
    
    def estimate_scraping_duration(self, selection: LocationSelection, settings: Dict[str, Any] = None) -> LocationEstimate:
        """Estimate scraping duration and result count for a location selection."""
        total_locations = 0
        total_searches = 0
        breakdown = {}
        
        # Default settings if not provided
        if not settings:
            settings = {
                "search_terms": ["dentist"],
                "request_delay": 1.0,
                "default_radius": 15000
            }
        
        search_terms_count = len(settings.get("search_terms", ["dentist"]))
        
        for city_name, city_config in selection.cities.items():
            city_searches = 0
            
            # City-level search
            if city_config.selected and city_config.city_level_search:
                city_searches += search_terms_count
                
                # Grid search multiplier
                if city_config.search_method == SearchMethod.GRID:
                    grid_multiplier = self._estimate_grid_points(settings)
                    city_searches *= grid_multiplier
            
            # District-level searches
            for district_name, district_config in city_config.districts.items():
                if district_config.selected:
                    district_searches = search_terms_count
                    
                    # Grid search multiplier
                    if district_config.search_method == SearchMethod.GRID:
                        grid_multiplier = self._estimate_grid_points(settings)
                        district_searches *= grid_multiplier
                    
                    city_searches += district_searches
            
            if city_searches > 0:
                total_locations += 1
                total_searches += city_searches
                breakdown[city_name] = city_searches
        
        # Estimate duration
        request_delay = settings.get("request_delay", 1.0)
        estimated_seconds = total_searches * (3 + request_delay)  # 3 seconds per API call + delay
        estimated_minutes = estimated_seconds / 60
        
        if estimated_minutes < 60:
            duration_str = f"{estimated_minutes:.0f} minutes"
        else:
            hours = estimated_minutes / 60
            remaining_minutes = estimated_minutes % 60
            duration_str = f"{hours:.0f}h {remaining_minutes:.0f}m"
        
        # Estimate results
        avg_results_per_search = self._estimate_results_per_search(settings.get("default_radius", 15000))
        min_results = int(total_searches * avg_results_per_search * 0.5)
        max_results = int(total_searches * avg_results_per_search * 1.5)
        results_range = f"{min_results:,}-{max_results:,} places"
        
        return LocationEstimate(
            total_locations=total_locations,
            total_searches=total_searches,
            estimated_duration=duration_str,
            estimated_results_range=results_range,
            breakdown=breakdown
        )
    
    def _estimate_grid_points(self, settings: Dict[str, Any]) -> int:
        """Estimate number of grid points based on grid settings."""
        grid_width = settings.get("grid_width_km", 5.0)
        grid_height = settings.get("grid_height_km", 5.0)
        grid_radius = settings.get("grid_radius_meters", 800) / 1000  # Convert to km
        
        # Rough estimation: grid points = area / (radius^2 * π) * overlap_factor
        area = grid_width * grid_height
        point_coverage = 3.14159 * (grid_radius ** 2)
        overlap_factor = 1.5  # Overlap for better coverage
        
        estimated_points = max(1, int(area / point_coverage * overlap_factor))
        return min(estimated_points, 50)  # Cap at reasonable number
    
    def _estimate_results_per_search(self, radius: int) -> float:
        """Estimate average results per search based on radius."""
        # Rough estimates based on typical dental clinic density
        if radius <= 5000:
            return 8.0  # Small radius, fewer results
        elif radius <= 15000:
            return 15.0  # Medium radius
        elif radius <= 30000:
            return 25.0  # Large radius
        else:
            return 35.0  # Very large radius
    
    def apply_batch_operation(self, operation: BatchOperation, current_selection: LocationSelection) -> LocationSelection:
        """Apply a batch operation to a location selection."""
        updated_selection = current_selection.copy(deep=True)
        
        for city_name in operation.targets:
            if city_name not in updated_selection.cities:
                continue
            
            city_config = updated_selection.cities[city_name]
            
            if operation.operation_type == "select_all":
                city_config.selected = True
                for district in city_config.districts.values():
                    district.selected = True
            
            elif operation.operation_type == "deselect_all":
                city_config.selected = False
                for district in city_config.districts.values():
                    district.selected = False
            
            elif operation.operation_type == "set_search_method":
                if operation.search_method:
                    city_config.search_method = operation.search_method
                    for district in city_config.districts.values():
                        district.search_method = operation.search_method
            
            elif operation.operation_type == "set_city_level_search":
                if operation.city_level_search is not None:
                    city_config.city_level_search = operation.city_level_search
        
        # Update totals
        updated_selection.total_selected = self._count_selected_locations(updated_selection)
        updated_selection.last_updated = datetime.now()
        
        return updated_selection
    
    def _count_selected_locations(self, selection: LocationSelection) -> int:
        """Count total selected locations."""
        count = 0
        for city_config in selection.cities.values():
            if city_config.selected:
                count += 1
            count += sum(1 for district in city_config.districts.values() if district.selected)
        return count
    
    def get_preset_selections(self) -> List[PresetSelection]:
        """Get predefined location selection presets."""
        available_cities = list(self.locations_data.get('cities', {}).keys())
        
        # Major cities (filter to only available ones)
        major_cities = [
            "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", 
            "Adana", "Konya", "Gaziantep", "Kayseri", "Mersin",
            "Eskişehir", "Diyarbakır", "Samsun", "Denizli", "Şanlıurfa"
        ]
        available_major = [city for city in major_cities if city in available_cities]
        
        # Coastal cities
        coastal_cities = [
            "İstanbul", "İzmir", "Antalya", "Mersin", "Samsun", "Trabzon",
            "Ordu", "Giresun", "Rize", "Artvin", "Hatay", "Adana",
            "Muğla", "Aydın", "Balıkesir", "Çanakkale", "Tekirdağ",
            "Kırklareli", "Zonguldak", "Bartın", "Kastamonu", "Sinop"
        ]
        available_coastal = [city for city in coastal_cities if city in available_cities]
        
        # Central Anatolia
        central_anatolia = [
            "Ankara", "Konya", "Kayseri", "Sivas", "Yozgat", "Kırıkkale",
            "Çorum", "Amasya", "Tokat", "Nevşehir", "Kırşehir", "Aksaray", "Niğde"
        ]
        available_central = [city for city in central_anatolia if city in available_cities]
        
        presets = [
            PresetSelection(
                id="major-cities",
                name=f"Major Cities ({len(available_major)})",
                description="Largest Turkish cities with high population density",
                cities=available_major,
                estimated_duration="2-3 hours",
                locations_count=len(available_major),
                search_settings={
                    "default_method": SearchMethod.STANDARD,
                    "city_level_only": True,
                    "radius": 25000
                }
            ),
            PresetSelection(
                id="coastal-cities", 
                name=f"Coastal Cities ({len(available_coastal)})",
                description="Cities with coastline access",
                cities=available_coastal,
                estimated_duration="4-6 hours",
                locations_count=len(available_coastal),
                search_settings={
                    "default_method": SearchMethod.STANDARD,
                    "city_level_only": False,
                    "radius": 20000
                }
            )
        ]
        
        # Add Central Anatolia if we have cities
        if available_central:
            presets.append(
                PresetSelection(
                    id="central-anatolia",
                    name=f"Central Anatolia ({len(available_central)})",
                    description="Inner Anatolia region cities",
                    cities=available_central,
                    estimated_duration="3-4 hours",
                    locations_count=len(available_central),
                    search_settings={
                        "default_method": SearchMethod.STANDARD,
                        "city_level_only": True,
                        "radius": 20000
                    }
                )
            )
        
        # Istanbul detailed (if available)
        if "İstanbul" in available_cities:
            istanbul_districts = len(self.locations_data['cities']['İstanbul'].get('districts', {}))
            presets.append(
                PresetSelection(
                    id="istanbul-detailed",
                    name=f"Istanbul Detailed ({istanbul_districts} districts)",
                    description="All Istanbul districts with comprehensive search",
                    cities=["İstanbul"],
                    estimated_duration="6-8 hours",
                    locations_count=istanbul_districts,
                    search_settings={
                        "default_method": SearchMethod.GRID,
                        "city_level_only": False,
                        "grid_width": 3,
                        "grid_height": 3,
                        "radius": 5000
                    }
                )
            )
        
        # All cities
        presets.append(
            PresetSelection(
                id="all-cities",
                name=f"All Cities ({len(available_cities)})",
                description="Complete coverage of all available cities",
                cities=available_cities,
                estimated_duration="20-40 hours",
                locations_count=len(available_cities),
                search_settings={
                    "default_method": SearchMethod.STANDARD,
                    "smart_method_selection": True,
                    "major_cities_grid": True
                }
            )
        )
        
        return presets
    
    def apply_preset_selection(self, preset_id: str) -> Optional[LocationSelection]:
        """Apply a preset selection and return the resulting LocationSelection."""
        presets = self.get_preset_selections()
        preset = next((p for p in presets if p.id == preset_id), None)
        
        if not preset:
            return None
        
        # Create location selection
        selection = LocationSelection()
        
        for city_name in preset.cities:
            city_data = self.get_city_data(city_name)
            if not city_data:
                continue
            
            # Determine search method
            search_method = SearchMethod.STANDARD
            city_level_search = True
            
            if preset.search_settings:
                if preset.search_settings.get("default_method") == SearchMethod.GRID:
                    search_method = SearchMethod.GRID
                city_level_search = preset.search_settings.get("city_level_only", True)
            
            # Create city config
            city_config = CityConfig(
                name=city_name,
                coordinates=(city_data.get('lat', 0), city_data.get('lng', 0)),
                selected=True,
                search_method=search_method,
                city_level_search=city_level_search
            )
            
            # Add districts if not city_level_only
            if not city_level_search:
                for district_name, district_data in city_data.get('districts', {}).items():
                    district_config = DistrictConfig(
                        name=district_name,
                        coordinates=(district_data.get('lat', 0), district_data.get('lng', 0)),
                        selected=True,
                        search_method=search_method
                    )
                    city_config.districts[district_name] = district_config
            
            selection.cities[city_name] = city_config
        
        # Update totals
        selection.total_selected = self._count_selected_locations(selection)
        selection.last_updated = datetime.now()
        
        return selection
    
    def get_location_statistics(self) -> Dict[str, Any]:
        """Get statistics about the location data."""
        cities_data = self.locations_data.get('cities', {})
        
        total_cities = len(cities_data)
        total_districts = sum(len(city.get('districts', {})) for city in cities_data.values())
        
        # Cities with most districts
        cities_by_district_count = sorted(
            [(name, len(data.get('districts', {}))) for name, data in cities_data.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Regional distribution (if region data available)
        regional_distribution = {}  # Would need additional data
        
        return {
            "total_cities": total_cities,
            "total_districts": total_districts,
            "average_districts_per_city": total_districts / total_cities if total_cities > 0 else 0,
            "cities_with_most_districts": cities_by_district_count,
            "regional_distribution": regional_distribution,
            "data_source": str(self.locations_file),
            "last_loaded": self.locations_data.get('metadata', {}).get('last_updated')
        }