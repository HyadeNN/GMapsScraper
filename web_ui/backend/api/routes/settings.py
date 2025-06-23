"""
Settings management API routes.
Handles configuration of scraper settings and system preferences.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.models.scraper import ScraperSettings, ApiKeyValidation, ApiKeyValidationResponse
from utils.integration import ScraperIntegration

router = APIRouter()

# Settings storage path
SETTINGS_DIR = Path(__file__).parent.parent.parent / "data" / "settings"
SETTINGS_FILE = SETTINGS_DIR / "ui_settings.json"


def ensure_settings_dir():
    """Ensure settings directory exists."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def load_ui_settings() -> Dict[str, Any]:
    """Load UI-specific settings from file."""
    ensure_settings_dir()
    
    if not SETTINGS_FILE.exists():
        return {}
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading UI settings: {e}")
        return {}


def save_ui_settings(settings: Dict[str, Any]):
    """Save UI-specific settings to file."""
    ensure_settings_dir()
    
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving UI settings: {e}")
        raise


get_scraper_integration = None


@router.get("/", response_model=ScraperSettings)
async def get_settings():
    """
    Get current scraper settings.
    Combines defaults from gmaps_scraper/config/settings.py with UI overrides.
    """
    try:
        # Load UI settings overrides
        ui_settings = load_ui_settings()
        
        # Get default settings from environment or gmaps_scraper
        default_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        
        # Create settings object with defaults and overrides
        settings = ScraperSettings(
            api_key=ui_settings.get('api_key', default_api_key),
            search_terms=ui_settings.get('search_terms', ["diş kliniği", "dentist"]),
            default_radius=ui_settings.get('default_radius', 15000),
            request_delay=ui_settings.get('request_delay', 1.0),
            max_retries=ui_settings.get('max_retries', 3),
            batch_size=ui_settings.get('batch_size', 20),
            storage_type=ui_settings.get('storage_type', 'json'),
            output_directory=ui_settings.get('output_directory', 'data'),
            language=ui_settings.get('language', 'tr'),
            region=ui_settings.get('region', 'tr'),
            grid_width_km=ui_settings.get('grid_width_km', 5.0),
            grid_height_km=ui_settings.get('grid_height_km', 5.0),
            grid_radius_meters=ui_settings.get('grid_radius_meters', 800),
            mongodb_uri=ui_settings.get('mongodb_uri'),
            mongodb_db=ui_settings.get('mongodb_db', 'dental_clinics'),
            mongodb_collection=ui_settings.get('mongodb_collection', 'places'),
            auto_save_interval=ui_settings.get('auto_save_interval', 2),
            log_level=ui_settings.get('log_level', 'INFO')
        )
        
        return settings
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")


@router.put("/", response_model=ScraperSettings)
async def update_settings(settings: ScraperSettings):
    """
    Update scraper settings.
    """
    try:
        # Validate API key if provided
        if settings.api_key:
            integration = get_scraper_integration()
            if integration:
                validation = await integration.validate_api_key(settings.api_key)
                if not validation["valid"]:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid API key: {validation['message']}"
                    )
        
        # Save settings to UI settings file
        settings_dict = settings.dict()
        save_ui_settings(settings_dict)
        
        return settings
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.patch("/")
async def update_partial_settings(updates: Dict[str, Any]):
    """
    Update specific settings fields without replacing all settings.
    """
    try:
        # Load current settings
        current_settings = await get_settings()
        current_dict = current_settings.dict()
        
        # Apply updates
        for key, value in updates.items():
            if key in current_dict:
                current_dict[key] = value
            else:
                raise HTTPException(status_code=400, detail=f"Unknown setting: {key}")
        
        # Validate and save
        updated_settings = ScraperSettings(**current_dict)
        save_ui_settings(current_dict)
        
        return {
            "success": True,
            "message": f"Updated {len(updates)} settings",
            "updated_fields": list(updates.keys()),
            "settings": updated_settings
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.post("/test-api-key", response_model=ApiKeyValidationResponse)
async def test_api_key(api_key_request: ApiKeyValidation):
    """
    Test if an API key is valid without saving it.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        result = await integration.validate_api_key(api_key_request.api_key)
        
        return ApiKeyValidationResponse(
            valid=result["valid"],
            message=result["message"],
            quota_info=result.get("quota_info")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API key test failed: {str(e)}")


@router.get("/defaults")
async def get_default_settings():
    """
    Get default settings without any user overrides.
    """
    try:
        defaults = ScraperSettings(
            api_key="",  # Never return actual API key in defaults
            search_terms=["diş kliniği", "dentist"],
            default_radius=15000,
            request_delay=1.0,
            max_retries=3,
            batch_size=20,
            storage_type="json",
            output_directory="data",
            language="tr",
            region="tr",
            grid_width_km=5.0,
            grid_height_km=5.0,
            grid_radius_meters=800,
            mongodb_uri=None,
            mongodb_db="dental_clinics",
            mongodb_collection="places",
            auto_save_interval=2,
            log_level="INFO"
        )
        
        return defaults
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get defaults: {str(e)}")


@router.post("/reset-to-defaults")
async def reset_to_defaults():
    """
    Reset all settings to default values.
    """
    try:
        # Get defaults
        defaults = await get_default_settings()
        
        # Preserve API key if it exists
        current_settings = load_ui_settings()
        if current_settings.get('api_key'):
            defaults.api_key = current_settings['api_key']
        
        # Save defaults
        save_ui_settings(defaults.dict())
        
        return {
            "success": True,
            "message": "Settings reset to defaults",
            "settings": defaults
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")


@router.get("/environment")
async def get_environment_info():
    """
    Get information about the environment and available features.
    """
    try:
        # Check for environment variables
        env_api_key = bool(os.getenv('GOOGLE_MAPS_API_KEY'))
        env_mongodb = bool(os.getenv('MONGODB_URI'))
        
        # Check for data directories
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
        profiles_dir = SETTINGS_DIR.parent / "profiles"
        
        return {
            "environment": {
                "has_env_api_key": env_api_key,
                "has_env_mongodb": env_mongodb,
                "data_directory_exists": data_dir.exists(),
                "profiles_directory_exists": profiles_dir.exists(),
                "settings_file_exists": SETTINGS_FILE.exists()
            },
            "paths": {
                "data_directory": str(data_dir),
                "settings_file": str(SETTINGS_FILE),
                "profiles_directory": str(profiles_dir)
            },
            "features": {
                "mongodb_support": True,
                "json_storage": True,
                "profile_management": True,
                "grid_search": True,
                "batch_operations": True
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get environment info: {str(e)}")


@router.get("/validation-rules")
async def get_validation_rules():
    """
    Get validation rules for settings fields.
    """
    try:
        return {
            "api_key": {
                "required": True,
                "min_length": 10,
                "description": "Google Places API key"
            },
            "search_terms": {
                "required": True,
                "min_items": 1,
                "max_items": 10,
                "description": "Search terms for Places API"
            },
            "default_radius": {
                "required": True,
                "min": 100,
                "max": 50000,
                "unit": "meters",
                "description": "Default search radius"
            },
            "request_delay": {
                "required": True,
                "min": 0.1,
                "max": 10.0,
                "unit": "seconds",
                "description": "Delay between API requests"
            },
            "max_retries": {
                "required": True,
                "min": 1,
                "max": 10,
                "description": "Maximum retry attempts for failed requests"
            },
            "batch_size": {
                "required": True,
                "min": 1,
                "max": 100,
                "description": "Number of places to process in each batch"
            },
            "grid_width_km": {
                "required": False,
                "min": 1.0,
                "max": 50.0,
                "unit": "kilometers",
                "description": "Grid search area width"
            },
            "grid_height_km": {
                "required": False,
                "min": 1.0,
                "max": 50.0,
                "unit": "kilometers", 
                "description": "Grid search area height"
            },
            "grid_radius_meters": {
                "required": False,
                "min": 100,
                "max": 5000,
                "unit": "meters",
                "description": "Search radius for each grid point"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation rules: {str(e)}")


@router.get("/presets")
async def get_settings_presets():
    """
    Get predefined settings presets for different use cases.
    """
    try:
        presets = {
            "development": {
                "name": "Development",
                "description": "Fast settings for development and testing",
                "settings": {
                    "request_delay": 0.5,
                    "batch_size": 10,
                    "max_retries": 2,
                    "log_level": "DEBUG"
                }
            },
            "production": {
                "name": "Production",
                "description": "Conservative settings for production use",
                "settings": {
                    "request_delay": 2.0,
                    "batch_size": 20,
                    "max_retries": 3,
                    "log_level": "INFO"
                }
            },
            "aggressive": {
                "name": "Aggressive",
                "description": "Fast scraping with higher API usage",
                "settings": {
                    "request_delay": 0.8,
                    "batch_size": 50,
                    "max_retries": 5,
                    "default_radius": 25000
                }
            },
            "conservative": {
                "name": "Conservative",
                "description": "Slow and safe scraping",
                "settings": {
                    "request_delay": 3.0,
                    "batch_size": 10,
                    "max_retries": 2,
                    "default_radius": 10000
                }
            }
        }
        
        return presets
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get presets: {str(e)}")


@router.post("/presets/{preset_name}/apply")
async def apply_settings_preset(preset_name: str):
    """
    Apply a predefined settings preset.
    """
    try:
        presets = await get_settings_presets()
        
        if preset_name not in presets:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
        
        preset = presets[preset_name]
        
        # Get current settings
        current_settings = await get_settings()
        current_dict = current_settings.dict()
        
        # Apply preset settings
        preset_settings = preset["settings"]
        for key, value in preset_settings.items():
            if key in current_dict:
                current_dict[key] = value
        
        # Save updated settings
        updated_settings = ScraperSettings(**current_dict)
        save_ui_settings(current_dict)
        
        return {
            "success": True,
            "message": f"Applied preset: {preset['name']}",
            "preset_name": preset_name,
            "applied_settings": preset_settings,
            "settings": updated_settings
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply preset: {str(e)}")