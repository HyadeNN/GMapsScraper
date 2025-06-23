"""
Location data models for the Google Maps Scraper Web UI.
These models handle city/district selection and search method configuration.
"""

from typing import Dict, List, Optional, Tuple, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SearchMethod(str, Enum):
    """Available search methods for locations."""
    SKIP = "skip"
    STANDARD = "standard" 
    GRID = "grid"


class DistrictConfig(BaseModel):
    """Configuration for a single district."""
    name: str
    coordinates: Tuple[float, float]  # (latitude, longitude)
    selected: bool = False
    search_method: SearchMethod = SearchMethod.STANDARD
    
    class Config:
        json_encoders = {
            tuple: list  # Convert tuples to lists for JSON serialization
        }


class CityConfig(BaseModel):
    """Configuration for a single city."""
    name: str
    coordinates: Tuple[float, float]  # (latitude, longitude)
    selected: bool = False
    search_method: SearchMethod = SearchMethod.SKIP
    city_level_search: bool = True  # Whether to search at city level
    districts: Dict[str, DistrictConfig] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            tuple: list  # Convert tuples to lists for JSON serialization
        }


class LocationSelection(BaseModel):
    """Complete location selection configuration."""
    cities: Dict[str, CityConfig] = Field(default_factory=dict)
    total_selected: int = 0
    estimated_duration: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class LocationHierarchy(BaseModel):
    """Full location hierarchy from locationsV2.json."""
    cities: Dict[str, Dict] = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)


class LocationSelectionUpdate(BaseModel):
    """Model for updating location selections."""
    city_name: str
    district_name: Optional[str] = None
    selected: bool
    search_method: Optional[SearchMethod] = None
    city_level_search: Optional[bool] = None


class BatchOperation(BaseModel):
    """Model for batch operations on locations."""
    operation_type: Literal[
        "select_all",
        "deselect_all", 
        "set_search_method",
        "set_city_level_search",
        "apply_preset"
    ]
    targets: List[str] = Field(default_factory=list)  # List of city names
    search_method: Optional[SearchMethod] = None
    city_level_search: Optional[bool] = None
    preset_name: Optional[str] = None


class LocationEstimate(BaseModel):
    """Estimation model for scraping duration and results."""
    total_locations: int
    total_searches: int  # Including city-level and district-level searches
    estimated_duration: str
    estimated_results_range: str  # e.g., "500-1500 places"
    breakdown: Dict[str, int] = Field(default_factory=dict)  # Per-city breakdown


class PresetSelection(BaseModel):
    """Predefined location selection presets."""
    id: str
    name: str
    description: str
    cities: List[str]
    estimated_duration: str
    locations_count: int
    search_settings: Dict = Field(default_factory=dict)