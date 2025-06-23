"""
Profile management models for saving and loading scraper configurations.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

from .scraper import ScraperSettings
from .location import LocationSelection


class ScrapingProfile(BaseModel):
    """A saved scraper configuration profile."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    settings: ScraperSettings
    locations: LocationSelection
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    is_default: bool = False
    tags: List[str] = Field(default_factory=list)  # For categorization
    
    # Statistics (populated when profile is used)
    usage_count: int = 0
    last_result_summary: Optional[Dict[str, Any]] = None


class ProfileCreateRequest(BaseModel):
    """Request to create a new profile."""
    name: str
    description: Optional[str] = None
    settings: ScraperSettings
    locations: LocationSelection
    is_default: bool = False
    tags: List[str] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    """Request to update an existing profile."""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[ScraperSettings] = None
    locations: Optional[LocationSelection] = None
    is_default: Optional[bool] = None
    tags: Optional[List[str]] = None


class ProfileListResponse(BaseModel):
    """Response containing list of profiles."""
    profiles: List[ScrapingProfile]
    default_profile_id: Optional[str] = None
    total_count: int


class PresetProfile(BaseModel):
    """Predefined profile template."""
    id: str
    name: str
    description: str
    estimated_duration: str
    locations_count: int
    settings_template: Dict[str, Any]
    locations_template: Dict[str, Any]
    category: str = "general"  # general, regional, detailed, quick
    
    
class ProfileImportRequest(BaseModel):
    """Request to import a profile from JSON."""
    profile_data: Dict[str, Any]
    overwrite_existing: bool = False


class ProfileExportResponse(BaseModel):
    """Response for profile export."""
    profile: ScrapingProfile
    export_format: str = "json"
    exported_at: datetime = Field(default_factory=datetime.now)


class ProfileStats(BaseModel):
    """Statistics about profile usage."""
    total_profiles: int
    most_used_profile: Optional[str] = None
    recent_profiles: List[str] = Field(default_factory=list)
    profiles_by_category: Dict[str, int] = Field(default_factory=dict)
    last_backup: Optional[datetime] = None


class ProfileBackup(BaseModel):
    """Profile backup data."""
    backup_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    profiles: List[ScrapingProfile]
    settings: Dict[str, Any] = Field(default_factory=dict)
    version: str = "2.0.0"