"""
Location management API routes.
Handles city/district data and location selection operations.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.models.location import (
    LocationHierarchy, LocationSelection, LocationSelectionUpdate,
    BatchOperation, LocationEstimate, PresetSelection, SearchMethod
)
from utils.integration import ScraperIntegration

router = APIRouter()


get_scraper_integration = None
get_location_service = None


@router.get("/", response_model=LocationHierarchy)
async def get_locations():
    """
    Get the complete location hierarchy (all cities and districts).
    Returns data from locationsV2.json with coordinates.
    """
    try:
        location_service = get_location_service()
        locations_data = location_service.get_locations_hierarchy()
        
        if not locations_data:
            raise HTTPException(status_code=404, detail="Location data not found")
        
        return LocationHierarchy(
            cities=locations_data.get('cities', {}),
            metadata=locations_data.get('metadata', {})
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load locations: {str(e)}")


@router.post("/estimate", response_model=LocationEstimate)
async def estimate_scraping_duration(selection: LocationSelection):
    """
    Estimate scraping duration and result count for given location selection.
    """
    try:
        # Calculate totals
        total_locations = 0
        total_searches = 0
        breakdown = {}
        
        for city_name, city_config in selection.cities.items():
            city_searches = 0
            
            # City-level search
            if city_config.selected and city_config.city_level_search:
                city_searches += 1
                total_searches += 1
            
            # District-level searches
            selected_districts = sum(
                1 for district in city_config.districts.values() 
                if district.selected
            )
            city_searches += selected_districts
            total_searches += selected_districts
            
            if city_searches > 0:
                total_locations += 1
                breakdown[city_name] = city_searches
        
        # Estimate duration (rough calculation)
        # Assume: 1 search = 3-5 seconds average (including delays)
        estimated_seconds = total_searches * 4
        estimated_minutes = estimated_seconds / 60
        
        if estimated_minutes < 60:
            duration_str = f"{estimated_minutes:.0f} minutes"
        else:
            hours = estimated_minutes / 60
            remaining_minutes = estimated_minutes % 60
            duration_str = f"{hours:.0f}h {remaining_minutes:.0f}m"
        
        # Estimate results (rough calculation)
        # Assume: 5-25 results per search on average
        min_results = total_searches * 5
        max_results = total_searches * 25
        results_range = f"{min_results}-{max_results} places"
        
        return LocationEstimate(
            total_locations=total_locations,
            total_searches=total_searches,
            estimated_duration=duration_str,
            estimated_results_range=results_range,
            breakdown=breakdown
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to estimate duration: {str(e)}")


@router.post("/update-selection")
async def update_location_selection(update: LocationSelectionUpdate):
    """
    Update selection status for a specific city or district.
    """
    try:
        # This endpoint would typically update a stored selection state
        # For now, we'll just validate the request and return success
        
        if update.district_name:
            message = f"Updated {update.city_name}/{update.district_name}: selected={update.selected}"
        else:
            message = f"Updated {update.city_name}: selected={update.selected}"
        
        if update.search_method:
            message += f", method={update.search_method}"
        
        return {"success": True, "message": message}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update selection: {str(e)}")


@router.post("/batch-operation")
async def perform_batch_operation(operation: BatchOperation):
    """
    Perform batch operations on multiple locations.
    """
    try:
        affected_count = len(operation.targets)
        
        operation_messages = {
            "select_all": f"Selected all locations in {affected_count} cities",
            "deselect_all": f"Deselected all locations in {affected_count} cities",
            "set_search_method": f"Set search method to {operation.search_method} for {affected_count} cities",
            "set_city_level_search": f"Set city-level search to {operation.city_level_search} for {affected_count} cities",
            "apply_preset": f"Applied preset '{operation.preset_name}' to {affected_count} cities"
        }
        
        message = operation_messages.get(operation.operation_type, "Unknown operation")
        
        return {
            "success": True,
            "message": message,
            "affected_cities": operation.targets,
            "operation_type": operation.operation_type
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch operation failed: {str(e)}")


@router.get("/presets", response_model=List[PresetSelection])
async def get_location_presets():
    """
    Get predefined location selection presets.
    """
    try:
        presets = [
            PresetSelection(
                id="major-cities",
                name="Major Cities (15)",
                description="İstanbul, Ankara, İzmir, Bursa, Antalya and other major cities",
                cities=[
                    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", 
                    "Konya", "Gaziantep", "Kayseri", "Mersin", "Eskişehir", 
                    "Diyarbakır", "Samsun", "Denizli", "Şanlıurfa"
                ],
                estimated_duration="2-3 hours",
                locations_count=15,
                search_settings={
                    "default_method": SearchMethod.STANDARD,
                    "city_level_only": True,
                    "radius": 25000
                }
            ),
            PresetSelection(
                id="coastal-cities",
                name="Coastal Cities (22)",
                description="Cities with coastline access",
                cities=[
                    "İstanbul", "İzmir", "Antalya", "Mersin", "Samsun", "Trabzon",
                    "Ordu", "Giresun", "Rize", "Artvin", "Hatay", "Adana",
                    "Muğla", "Aydın", "Balıkesir", "Çanakkale", "Tekirdağ",
                    "Kırklareli", "Zonguldak", "Bartın", "Kastamonu", "Sinop"
                ],
                estimated_duration="4-5 hours",
                locations_count=22,
                search_settings={
                    "default_method": SearchMethod.STANDARD,
                    "city_level_only": False,
                    "radius": 20000
                }
            ),
            PresetSelection(
                id="istanbul-detailed",
                name="Istanbul Detailed",
                description="All Istanbul districts with grid search",
                cities=["İstanbul"],
                estimated_duration="6-8 hours",
                locations_count=39,
                search_settings={
                    "default_method": SearchMethod.GRID,
                    "city_level_only": False,
                    "grid_width": 3,
                    "grid_height": 3,
                    "radius": 5000
                }
            ),
            PresetSelection(
                id="central-anatolia",
                name="Central Anatolia (13)",
                description="Inner Anatolia region cities",
                cities=[
                    "Ankara", "Konya", "Kayseri", "Sivas", "Yozgat", "Kırıkkale",
                    "Çorum", "Amasya", "Tokat", "Nevşehir", "Kırşehir", "Aksaray", "Niğde"
                ],
                estimated_duration="3-4 hours",
                locations_count=13,
                search_settings={
                    "default_method": SearchMethod.STANDARD,
                    "city_level_only": True,
                    "radius": 20000
                }
            )
        ]
        
        return presets
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load presets: {str(e)}")


@router.post("/apply-preset/{preset_id}")
async def apply_location_preset(preset_id: str):
    """
    Apply a predefined location preset to current selection.
    """
    try:
        # Get the preset
        presets = await get_location_presets()
        preset = next((p for p in presets if p.id == preset_id), None)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
        
        # In a real implementation, this would update the current selection state
        # For now, we'll return the preset configuration
        
        return {
            "success": True,
            "message": f"Applied preset: {preset.name}",
            "preset": preset,
            "cities_selected": preset.cities,
            "settings_applied": preset.search_settings
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply preset: {str(e)}")