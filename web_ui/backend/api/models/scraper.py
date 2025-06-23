"""
Scraper configuration and progress models for the Google Maps Scraper Web UI.
"""

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ScraperSettings(BaseModel):
    """Scraper configuration settings (mirrors gmaps_scraper/config/settings.py)."""
    api_key: str
    search_terms: List[str] = Field(default=["diş kliniği", "dentist"])
    default_radius: int = Field(default=15000, ge=100, le=50000)  # meters
    request_delay: float = Field(default=1.0, ge=0.1, le=10.0)  # seconds
    max_retries: int = Field(default=3, ge=1, le=10)
    batch_size: int = Field(default=20, ge=1, le=100)
    storage_type: Literal["json", "mongodb"] = "json"
    output_directory: str = "data"
    language: str = "tr"
    region: str = "tr"
    
    # Grid search specific settings
    grid_width_km: float = Field(default=5.0, ge=1.0, le=50.0)
    grid_height_km: float = Field(default=5.0, ge=1.0, le=50.0) 
    grid_radius_meters: int = Field(default=800, ge=100, le=5000)
    
    # MongoDB settings (optional)
    mongodb_uri: Optional[str] = None
    mongodb_db: str = "dental_clinics"
    mongodb_collection: str = "places"
    
    # UI specific settings
    auto_save_interval: int = Field(default=2, ge=1, le=10)  # seconds
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class ProgressStatus(str, Enum):
    """Current status of the scraping operation."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPING = "stopping"


class CurrentProgress(BaseModel):
    """Real-time progress information."""
    status: ProgressStatus = ProgressStatus.IDLE
    current_city: Optional[str] = None
    current_district: Optional[str] = None
    current_search_method: Optional[str] = None
    completed_locations: int = 0
    total_locations: int = 0
    completion_percentage: float = 0.0
    estimated_time_remaining: Optional[str] = None
    processing_speed: Optional[str] = None  # "2.3 locations/min"
    results_found: int = 0
    errors_encountered: int = 0
    last_save_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    elapsed_time: Optional[str] = None


class LogLevel(str, Enum):
    """Log message severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class LogMessage(BaseModel):
    """Individual log message."""
    timestamp: datetime = Field(default_factory=datetime.now)
    level: LogLevel
    message: str
    location: Optional[str] = None  # "İstanbul/Kadıköy"
    details: Optional[Dict[str, Any]] = None  # Additional context


class ScrapingOperation(BaseModel):
    """Complete scraping operation configuration."""
    operation_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    settings: ScraperSettings
    locations: Dict[str, Any]  # LocationSelection from location.py
    profile_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ScrapingResult(BaseModel):
    """Results from a completed scraping operation."""
    operation_id: str
    total_found: int
    by_location: Dict[str, int] = Field(default_factory=dict)  # location -> count
    by_search_term: Dict[str, int] = Field(default_factory=dict)  # term -> count
    files_created: List[str] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


class ApiKeyValidation(BaseModel):
    """API key validation request."""
    api_key: str


class ApiKeyValidationResponse(BaseModel):
    """API key validation response."""
    valid: bool
    message: str
    quota_info: Optional[Dict[str, Any]] = None
    tested_at: datetime = Field(default_factory=datetime.now)


class ScraperControl(BaseModel):
    """Scraper control commands."""
    action: Literal["start", "pause", "resume", "stop"]
    operation_id: Optional[str] = None


class ScraperStatus(BaseModel):
    """Current scraper status response."""
    status: ProgressStatus
    operation_id: Optional[str] = None
    progress: CurrentProgress
    can_start: bool = True
    can_pause: bool = False
    can_stop: bool = False
    message: Optional[str] = None