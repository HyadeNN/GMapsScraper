"""
Integration service for connecting the web UI with the existing gmaps_scraper package.
This service handles the actual scraping operations and data management.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import threading
import time

# Add the gmaps_scraper package to Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from gmaps_scraper.core.scraper import GooglePlacesScraper
    from gmaps_scraper.core.data_processor import DataProcessor
    from gmaps_scraper.core.storage import get_storage
    from gmaps_scraper.config.settings import API_KEY, SEARCH_TERMS
    from gmaps_scraper.utils.helpers import load_json_file
    from gmaps_scraper.utils.grid_search import grid_search_places
except ImportError as e:
    print(f"Error importing gmaps_scraper: {e}")
    # Create dummy classes for development
    class GooglePlacesScraper:
        def __init__(self, api_key=None): pass
    class DataProcessor:
        def __init__(self): pass
    def get_storage(): return None
    def load_json_file(path): return {}
    def grid_search_places(*args, **kwargs): return []
    API_KEY = None
    SEARCH_TERMS = []

from api.models.scraper import ProgressStatus, CurrentProgress, LogMessage, LogLevel
from api.models.location import LocationSelection, CityConfig, DistrictConfig, SearchMethod


class ScraperIntegration:
    """Main integration class for web UI and gmaps_scraper."""
    
    def __init__(self):
        self.current_operation_id: Optional[str] = None
        self.current_progress = CurrentProgress()
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.scraper_thread: Optional[threading.Thread] = None
        
        # Event callbacks for real-time updates
        self.progress_callbacks: List[Callable] = []
        self.log_callbacks: List[Callable] = []
        
        # Location data cache
        self.locations_data: Dict = {}
        
        # Current scraping components
        self.scraper: Optional[GooglePlacesScraper] = None
        self.processor: Optional[DataProcessor] = None
        self.storage = None
        
    async def load_locations(self) -> Dict:
        """Load location data from locationsV2.json."""
        try:
            locations_path = Path(__file__).parent.parent.parent.parent / "gmaps_scraper" / "config" / "locationsV2.json"
            
            if locations_path.exists():
                with open(locations_path, 'r', encoding='utf-8') as f:
                    self.locations_data = json.load(f)
                    
                # Add metadata
                cities_count = len(self.locations_data.get('cities', {}))
                districts_count = sum(
                    len(city_data.get('districts', {})) 
                    for city_data in self.locations_data.get('cities', {}).values()
                )
                
                self.locations_data['metadata'] = {
                    'total_cities': cities_count,
                    'total_districts': districts_count,
                    'last_updated': datetime.now().isoformat(),
                    'source_file': str(locations_path)
                }
                
                await self._log(LogLevel.INFO, f"Loaded {cities_count} cities and {districts_count} districts")
                return self.locations_data
            else:
                await self._log(LogLevel.ERROR, f"Location file not found: {locations_path}")
                return {}
                
        except Exception as e:
            await self._log(LogLevel.ERROR, f"Error loading locations: {str(e)}")
            return {}
    
    def get_locations(self) -> Dict:
        """Get cached location data."""
        return self.locations_data
    
    async def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate Google Places API key."""
        try:
            # Create a test scraper instance
            test_scraper = GooglePlacesScraper(api_key=api_key)
            
            # Try a simple search to validate the key
            test_location = (41.0082, 28.9784)  # Istanbul coordinates
            test_results = test_scraper.search_places("test", test_location, radius=1000)
            
            return {
                "valid": True,
                "message": "API key is valid and working",
                "quota_info": {
                    "test_successful": True,
                    "results_count": len(test_results) if test_results else 0
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            if "INVALID_REQUEST" in error_msg or "REQUEST_DENIED" in error_msg:
                return {
                    "valid": False,
                    "message": "API key is invalid or permissions are insufficient",
                    "quota_info": None
                }
            elif "OVER_QUERY_LIMIT" in error_msg:
                return {
                    "valid": True,
                    "message": "API key is valid but quota is exceeded",
                    "quota_info": {"quota_exceeded": True}
                }
            else:
                return {
                    "valid": False,
                    "message": f"API validation failed: {error_msg}",
                    "quota_info": None
                }
    
    async def start_scraping(self, operation_id: str, settings: Dict, locations: Dict) -> bool:
        """Start a scraping operation."""
        if self.is_running:
            await self._log(LogLevel.WARNING, "Scraping is already running")
            return False
        
        try:
            total_locations = self._count_selected_locations(locations)
            await self._log(LogLevel.INFO, f"DEBUG: Found {total_locations} selected locations")
            await self._log(LogLevel.INFO, f"DEBUG: Locations data: {list(locations.get('cities', {}).keys())}")
            
            if total_locations == 0:
                await self._log(LogLevel.WARNING, "No locations selected for scraping")
                return False
            
            self.current_operation_id = operation_id
            self.should_stop = False
            self.is_paused = False
            self.is_running = True
            
            # Initialize progress
            self.current_progress = CurrentProgress(
                status=ProgressStatus.RUNNING,
                start_time=datetime.now(),
                total_locations=total_locations
            )
            
            await self._log(LogLevel.INFO, f"Starting scraping operation: {operation_id}")
            await self._update_progress()
            
            # Start scraping in a separate thread
            self.scraper_thread = threading.Thread(
                target=self._run_scraping_sync,
                args=(settings, locations),
                daemon=True
            )
            self.scraper_thread.start()
            
            return True
            
        except Exception as e:
            await self._log(LogLevel.ERROR, f"Failed to start scraping: {str(e)}")
            self.is_running = False
            self.current_progress.status = ProgressStatus.ERROR
            await self._update_progress()
            return False
    
    def _run_scraping_sync(self, settings: Dict, locations: Dict):
        """Run the actual scraping operation synchronously (in thread)."""
        try:
            # Initialize scraper components
            self.scraper = GooglePlacesScraper(api_key=settings['api_key'])
            self.processor = DataProcessor()
            self.storage = get_storage()
            
            # Configure scraper settings
            self.scraper.batch_size = settings.get('batch_size', 20)
            
            total_processed = 0
            search_terms = settings.get('search_terms', ['dentist'])
            
            # Process each selected city
            for city_name, city_config in locations.get('cities', {}).items():
                if self.should_stop:
                    break
                    
                # Check if city is selected (has search_method or districts)
                if not city_config.get('search_method') and not city_config.get('districts'):
                    continue
                
                # Wait if paused
                while self.is_paused and not self.should_stop:
                    time.sleep(1)
                
                if self.should_stop:
                    break
                
                asyncio.run(self._process_city(
                    city_name, city_config, settings, search_terms
                ))
                
                total_processed += 1
                self.current_progress.completed_locations = total_processed
                self.current_progress.completion_percentage = (
                    total_processed / self.current_progress.total_locations * 100
                )
                asyncio.run(self._update_progress())
            
            # Complete the operation
            if not self.should_stop:
                self.current_progress.status = ProgressStatus.COMPLETED
                asyncio.run(self._log(LogLevel.SUCCESS, "Scraping operation completed successfully"))
            else:
                self.current_progress.status = ProgressStatus.IDLE
                asyncio.run(self._log(LogLevel.INFO, "Scraping operation stopped by user"))
            
        except Exception as e:
            self.current_progress.status = ProgressStatus.ERROR
            asyncio.run(self._log(LogLevel.ERROR, f"Scraping error: {str(e)}"))
        
        finally:
            self.is_running = False
            self.is_paused = False
            asyncio.run(self._update_progress())
    
    async def _process_city(self, city_name: str, city_config: Dict, settings: Dict, search_terms: List[str]):
        """Process a single city with its districts."""
        self.current_progress.current_city = city_name
        self.current_progress.current_district = None
        await self._update_progress()
        
        city_data = self.locations_data['cities'].get(city_name, {})
        city_coords = (city_data.get('lat'), city_data.get('lng'))
        
        # City-level search if city has search_method but no districts selected
        city_search_method = city_config.get('search_method')
        has_selected_districts = any(d.get('search_method') for d in city_config.get('districts', {}).values())
        
        if city_search_method and not has_selected_districts:
            await self._log(LogLevel.INFO, f"Searching city level: {city_name} ({city_search_method})")
            
            for term in search_terms:
                if self.should_stop:
                    break
                    
                await self._perform_search(
                    term, city_coords, city_name, None, city_search_method, settings
                )
        
        # District-level searches
        for district_name, district_config in city_config.get('districts', {}).items():
            if self.should_stop:
                break
                
            if not district_config.get('search_method'):
                continue
            
            # Wait if paused
            while self.is_paused and not self.should_stop:
                await asyncio.sleep(1)
            
            if self.should_stop:
                break
            
            self.current_progress.current_district = district_name
            await self._update_progress()
            
            district_data = city_data.get('districts', {}).get(district_name, {})
            district_coords = (district_data.get('lat'), district_data.get('lng'))
            search_method = district_config.get('search_method', 'standard')
            
            await self._log(LogLevel.INFO, f"Searching district: {city_name}/{district_name} ({search_method})")
            
            for term in search_terms:
                if self.should_stop:
                    break
                    
                await self._perform_search(
                    term, district_coords, city_name, district_name, search_method, settings
                )
    
    async def _perform_search(self, term: str, coords: tuple, city: str, district: Optional[str], 
                            method: str, settings: Dict):
        """Perform a single search operation."""
        if not coords[0] or not coords[1]:
            await self._log(LogLevel.WARNING, f"Invalid coordinates for {city}/{district or 'city'}")
            return
        
        try:
            if method == 'grid':
                # Grid search
                places = grid_search_places(
                    self.scraper,
                    term,
                    coords,
                    area_width_km=settings.get('grid_width_km', 5.0),
                    area_height_km=settings.get('grid_height_km', 5.0),
                    search_radius_meters=settings.get('grid_radius_meters', 800),
                    storage=self.storage,
                    processor=self.processor,
                    city=city,
                    district=district
                )
            else:
                # Standard search
                places = self.scraper.fetch_places_with_details(
                    term,
                    coords,
                    radius=settings.get('default_radius', 15000),
                    storage=self.storage,
                    processor=self.processor,
                    search_term=term,
                    city=city,
                    district=district
                )
            
            results_count = len(places) if places else 0
            self.current_progress.results_found += results_count
            
            await self._log(
                LogLevel.SUCCESS, 
                f"Found {results_count} results for '{term}' in {city}/{district or 'city'}",
                location=f"{city}/{district or 'city'}"
            )
            
            # Add delay between searches
            delay = settings.get('request_delay', 1.0)
            if delay > 0:
                await asyncio.sleep(delay)
                
        except Exception as e:
            self.current_progress.errors_encountered += 1
            await self._log(
                LogLevel.ERROR, 
                f"Search failed for '{term}' in {city}/{district or 'city'}: {str(e)}",
                location=f"{city}/{district or 'city'}"
            )
    
    async def pause_scraping(self) -> bool:
        """Pause the current scraping operation."""
        if not self.is_running or self.is_paused:
            return False
        
        self.is_paused = True
        self.current_progress.status = ProgressStatus.PAUSED
        await self._log(LogLevel.INFO, "Scraping operation paused")
        await self._update_progress()
        return True
    
    async def resume_scraping(self) -> bool:
        """Resume a paused scraping operation."""
        if not self.is_running or not self.is_paused:
            return False
        
        self.is_paused = False
        self.current_progress.status = ProgressStatus.RUNNING
        await self._log(LogLevel.INFO, "Scraping operation resumed")
        await self._update_progress()
        return True
    
    async def stop_scraping(self) -> bool:
        """Stop the current scraping operation."""
        if not self.is_running:
            return False
        
        self.should_stop = True
        self.current_progress.status = ProgressStatus.STOPPING
        await self._log(LogLevel.INFO, "Stopping scraping operation...")
        await self._update_progress()
        
        # Wait for thread to finish (with timeout)
        if self.scraper_thread and self.scraper_thread.is_alive():
            self.scraper_thread.join(timeout=5.0)
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scraper status."""
        return {
            "status": self.current_progress.status,
            "operation_id": self.current_operation_id,
            "progress": self.current_progress.dict(),
            "can_start": not self.is_running,
            "can_pause": self.is_running and not self.is_paused,
            "can_stop": self.is_running,
            "can_resume": self.is_running and self.is_paused
        }
    
    def _count_selected_locations(self, locations: Dict) -> int:
        """Count total selected locations for progress tracking."""
        count = 0
        for city_config in locations.get('cities', {}).values():
            # Count city if it has search_method
            if city_config.get('search_method'):
                count += 1
                
            # Count selected districts
            for district_config in city_config.get('districts', {}).values():
                if district_config.get('search_method'):
                    count += 1
        
        return count
    
    async def _log(self, level: LogLevel, message: str, location: Optional[str] = None):
        """Send log message to all registered callbacks."""
        log_msg = LogMessage(
            level=level,
            message=message,
            location=location
        )
        
        for callback in self.log_callbacks:
            try:
                await callback(log_msg)
            except Exception as e:
                print(f"Error in log callback: {e}")
    
    async def _update_progress(self):
        """Send progress update to all registered callbacks."""
        # Calculate processing speed
        if self.current_progress.start_time and self.current_progress.completed_locations > 0:
            elapsed = datetime.now() - self.current_progress.start_time
            elapsed_minutes = elapsed.total_seconds() / 60
            if elapsed_minutes > 0:
                speed = self.current_progress.completed_locations / elapsed_minutes
                self.current_progress.processing_speed = f"{speed:.1f} locations/min"
                
                # Estimate remaining time
                if speed > 0 and self.current_progress.total_locations > self.current_progress.completed_locations:
                    remaining_locations = self.current_progress.total_locations - self.current_progress.completed_locations
                    remaining_minutes = remaining_locations / speed
                    self.current_progress.estimated_time_remaining = f"{remaining_minutes:.0f} minutes"
        
        for callback in self.progress_callbacks:
            try:
                await callback(self.current_progress)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def add_progress_callback(self, callback: Callable):
        """Add a callback for progress updates."""
        self.progress_callbacks.append(callback)
    
    def add_log_callback(self, callback: Callable):
        """Add a callback for log messages."""
        self.log_callbacks.append(callback)
    
    async def cleanup(self):
        """Cleanup resources when shutting down."""
        if self.is_running:
            await self.stop_scraping()
        
        self.progress_callbacks.clear()
        self.log_callbacks.clear()