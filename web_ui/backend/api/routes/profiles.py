"""
Profile management API routes.
Handles saving, loading, and managing scraper configuration profiles.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.models.profile import (
    ScrapingProfile, ProfileCreateRequest, ProfileUpdateRequest, 
    ProfileListResponse, PresetProfile, ProfileImportRequest,
    ProfileExportResponse, ProfileStats
)

router = APIRouter()

get_profile_service = None


@router.get("/", response_model=ProfileListResponse)
async def get_profiles():
    """Get list of all saved profiles."""
    try:
        profile_service = get_profile_service()
        profiles = profile_service.get_all_profiles()
        default_profile = profile_service.get_default_profile()
        
        return ProfileListResponse(
            profiles=profiles,
            default_profile_id=default_profile.id if default_profile else None,
            total_count=len(profiles)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load profiles: {str(e)}")


@router.post("/", response_model=ScrapingProfile)
async def create_profile(profile_request: ProfileCreateRequest):
    """Create a new scraping profile."""
    try:
        profile_service = get_profile_service()
        return profile_service.create_profile(profile_request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {str(e)}")


@router.get("/{profile_id}", response_model=ScrapingProfile)
async def get_profile(profile_id: str):
    """Get a specific profile by ID."""
    try:
        profile_service = get_profile_service()
        profile = profile_service.get_profile_by_id(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        # Update usage
        profile_service.update_profile_usage(profile_id)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.put("/{profile_id}", response_model=ScrapingProfile)
async def update_profile(profile_id: str, update_request: ProfileUpdateRequest):
    """Update an existing profile."""
    try:
        profile_service = get_profile_service()
        updated_profile = profile_service.update_profile(profile_id, update_request)
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        return updated_profile
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    try:
        profile_service = get_profile_service()
        success = profile_service.delete_profile(profile_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        return {
            "success": True,
            "message": f"Profile deleted successfully",
            "deleted_profile_id": profile_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")


@router.post("/{profile_id}/duplicate", response_model=ScrapingProfile)
async def duplicate_profile(profile_id: str, new_name: Optional[str] = None):
    """Create a duplicate of an existing profile."""
    try:
        profile_service = get_profile_service()
        duplicate = profile_service.duplicate_profile(profile_id, new_name)
        
        if not duplicate:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        return duplicate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate profile: {str(e)}")


@router.post("/{profile_id}/set-default")
async def set_default_profile(profile_id: str):
    """Set a profile as the default."""
    try:
        profile_service = get_profile_service()
        success = profile_service.set_default_profile(profile_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        return {
            "success": True,
            "message": f"Profile set as default",
            "default_profile_id": profile_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set default profile: {str(e)}")


@router.get("/presets/list", response_model=List[PresetProfile])
async def get_preset_profiles():
    """Get predefined profile presets."""
    try:
        presets = [
            PresetProfile(
                id="quick-major-cities",
                name="Quick Scan - Major Cities",
                description="15 largest cities, city-level only, standard search",
                estimated_duration="2-3 hours",
                locations_count=15,
                settings_template={
                    "search_terms": ["diş kliniği", "dentist"],
                    "default_radius": 25000,
                    "request_delay": 1.0,
                    "batch_size": 20,
                    "storage_type": "json"
                },
                locations_template={
                    "cities": [
                        "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", 
                        "Adana", "Konya", "Gaziantep", "Kayseri", "Mersin", 
                        "Eskişehir", "Diyarbakır", "Samsun", "Denizli", "Şanlıurfa"
                    ],
                    "default_method": "standard",
                    "city_level_only": True
                },
                category="quick"
            ),
            PresetProfile(
                id="detailed-istanbul",
                name="Detailed Istanbul",
                description="All Istanbul districts with grid search",
                estimated_duration="6-8 hours",
                locations_count=39,
                settings_template={
                    "search_terms": ["diş kliniği", "dentist", "ortodontist"],
                    "default_radius": 5000,
                    "request_delay": 1.5,
                    "batch_size": 15,
                    "storage_type": "json",
                    "grid_width_km": 3.0,
                    "grid_height_km": 3.0,
                    "grid_radius_meters": 500
                },
                locations_template={
                    "cities": ["İstanbul"],
                    "default_method": "grid",
                    "city_level_only": False,
                    "all_districts": True
                },
                category="detailed"
            ),
            PresetProfile(
                id="coastal-comprehensive",
                name="Coastal Cities Comprehensive",
                description="All coastal cities with mixed search methods",
                estimated_duration="8-12 hours",
                locations_count=22,
                settings_template={
                    "search_terms": ["diş kliniği", "dentist"],
                    "default_radius": 20000,
                    "request_delay": 1.2,
                    "batch_size": 20,
                    "storage_type": "json"
                },
                locations_template={
                    "cities": [
                        "İstanbul", "İzmir", "Antalya", "Mersin", "Samsun", 
                        "Trabzon", "Ordu", "Giresun", "Rize", "Hatay", 
                        "Adana", "Muğla", "Aydın", "Balıkesir", "Çanakkale"
                    ],
                    "default_method": "standard",
                    "major_cities_grid": True
                },
                category="regional"
            )
        ]
        
        return presets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load presets: {str(e)}")


@router.post("/presets/{preset_id}/apply", response_model=ScrapingProfile)
async def apply_preset_profile(preset_id: str, profile_name: Optional[str] = None):
    """Create a new profile from a preset."""
    try:
        presets = await get_preset_profiles()
        preset = next((p for p in presets if p.id == preset_id), None)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
        
        profile_service = get_profile_service()
        
        # Generate profile name
        name = profile_name or preset.name
        profiles = profile_service.get_all_profiles()
        counter = 1
        original_name = name
        while any(p.name == name for p in profiles):
            name = f"{original_name} ({counter})"
            counter += 1
        
        # Create settings from template
        from api.models.scraper import ScraperSettings
        from api.models.location import LocationSelection
        
        settings = ScraperSettings(
            api_key="",  # Will be set by user
            **preset.settings_template
        )
        
        # Create basic location selection
        locations = LocationSelection()
        
        # Create profile request
        profile_request = ProfileCreateRequest(
            name=name,
            description=f"Created from preset: {preset.description}",
            settings=settings,
            locations=locations,
            tags=[preset.category, "preset"]
        )
        
        return profile_service.create_profile(profile_request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply preset: {str(e)}")


@router.get("/stats/summary", response_model=ProfileStats)
async def get_profile_stats():
    """Get statistics about profile usage."""
    try:
        profile_service = get_profile_service()
        stats = profile_service.get_profile_statistics()
        
        return ProfileStats(
            total_profiles=stats["total_profiles"],
            most_used_profile=stats["most_used_profile"],
            recent_profiles=stats["recent_profiles"],
            profiles_by_category=stats["profiles_by_category"],
            last_backup=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/export/{profile_id}", response_model=ProfileExportResponse)
async def export_profile(profile_id: str):
    """Export a profile to JSON format."""
    try:
        profile_service = get_profile_service()
        export_data = profile_service.export_profile(profile_id)
        
        if not export_data:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        
        return ProfileExportResponse(
            profile=ScrapingProfile(**export_data["profile"]),
            export_format="json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export profile: {str(e)}")


@router.post("/import", response_model=ScrapingProfile)
async def import_profile(import_request: ProfileImportRequest):
    """Import a profile from JSON data."""
    try:
        profile_service = get_profile_service()
        return profile_service.import_profile(
            import_request.profile_data, 
            import_request.overwrite_existing
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import profile: {str(e)}")


@router.get("/search")
async def search_profiles(q: Optional[str] = None, tags: Optional[str] = None):
    """Search profiles by name, description, or tags."""
    try:
        profile_service = get_profile_service()
        tag_list = tags.split(",") if tags else None
        
        results = profile_service.search_profiles(query=q, tags=tag_list)
        
        return {
            "results": results,
            "total_found": len(results),
            "query": q,
            "tags": tag_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/backup")
async def backup_profiles():
    """Create a backup of all profiles."""
    try:
        profile_service = get_profile_service()
        backup_data = profile_service.backup_profiles()
        
        return {
            "success": True,
            "message": "Profiles backed up successfully",
            "backup": backup_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/restore")
async def restore_profiles(backup_data: dict, merge: bool = False):
    """Restore profiles from backup data."""
    try:
        profile_service = get_profile_service()
        restored_count = profile_service.restore_profiles(backup_data, merge)
        
        return {
            "success": True,
            "message": f"Restored {restored_count} profiles",
            "restored_count": restored_count,
            "merge_mode": merge
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")