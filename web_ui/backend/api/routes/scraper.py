"""
Scraper control API routes.
Handles starting, stopping, pausing scraping operations and progress monitoring.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.models.scraper import (
    ScrapingOperation, ScraperControl, ScraperStatus, CurrentProgress,
    ScrapingResult, ApiKeyValidation, ApiKeyValidationResponse
)
from utils.integration import ScraperIntegration

router = APIRouter()


get_scraper_integration = None


@router.post("/start")
async def start_scraping(operation: ScrapingOperation):
    """
    Start a new scraping operation.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        # Validate API key first
        api_key = operation.settings.api_key
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        validation = await integration.validate_api_key(api_key)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid API key: {validation['message']}")
        
        # Start the scraping operation
        success = await integration.start_scraping(
            operation_id=operation.operation_id,
            settings=operation.settings.dict(),
            locations=operation.locations
        )
        
        if not success:
            raise HTTPException(status_code=409, detail="Could not start scraping - operation may already be running")
        
        return {
            "success": True,
            "message": "Scraping started successfully",
            "operation_id": operation.operation_id,
            "status": "running"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")


@router.post("/control")
async def control_scraper(control: ScraperControl):
    """
    Control scraper operation (pause, resume, stop).
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        success = False
        message = ""
        
        if control.action == "pause":
            success = await integration.pause_scraping()
            message = "Scraping paused" if success else "Could not pause scraping"
        
        elif control.action == "resume":
            success = await integration.resume_scraping()
            message = "Scraping resumed" if success else "Could not resume scraping"
        
        elif control.action == "stop":
            success = await integration.stop_scraping()
            message = "Scraping stopped" if success else "Could not stop scraping"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {control.action}")
        
        if not success:
            raise HTTPException(status_code=409, detail=message)
        
        return {
            "success": True,
            "message": message,
            "action": control.action,
            "operation_id": control.operation_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to control scraper: {str(e)}")


@router.get("/status", response_model=ScraperStatus)
async def get_scraper_status():
    """
    Get current scraper status and progress.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        status_data = integration.get_status()
        
        return ScraperStatus(
            status=status_data["status"],
            operation_id=status_data.get("operation_id"),
            progress=CurrentProgress(**status_data["progress"]),
            can_start=status_data["can_start"],
            can_pause=status_data["can_pause"],
            can_stop=status_data["can_stop"],
            message=status_data.get("message")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/results", response_model=ScrapingResult)
async def get_scraping_results(operation_id: str = None):
    """
    Get results from current or specified scraping operation.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        # For now, return basic progress info as results
        # In a full implementation, this would fetch actual result data
        progress = integration.current_progress
        
        return ScrapingResult(
            operation_id=operation_id or integration.current_operation_id or "unknown",
            total_found=progress.results_found,
            by_location={
                f"{progress.current_city}/{progress.current_district or 'city'}": progress.results_found
            } if progress.current_city else {},
            by_search_term={},  # Would be populated from actual results
            files_created=[],   # Would be populated from storage
            start_time=progress.start_time or None,
            end_time=None,
            duration=progress.elapsed_time,
            errors=[]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.post("/validate-api-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(validation_request: ApiKeyValidation):
    """
    Validate Google Places API key.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        result = await integration.validate_api_key(validation_request.api_key)
        
        return ApiKeyValidationResponse(
            valid=result["valid"],
            message=result["message"],
            quota_info=result.get("quota_info")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API validation failed: {str(e)}")


@router.get("/health")
async def scraper_health_check():
    """
    Check if scraper integration is healthy and responsive.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            return {"healthy": False, "message": "Scraper integration not available"}
        
        # Check if locations are loaded
        locations = integration.get_locations()
        locations_loaded = bool(locations and locations.get('cities'))
        
        return {
            "healthy": True,
            "message": "Scraper integration is healthy",
            "locations_loaded": locations_loaded,
            "cities_count": len(locations.get('cities', {})) if locations_loaded else 0,
            "integration_status": "ready"
        }
    
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Health check failed: {str(e)}",
            "integration_status": "error"
        }


@router.get("/operations/history")
async def get_operations_history():
    """
    Get history of recent scraping operations.
    """
    try:
        # In a full implementation, this would return actual operation history
        # For now, return a placeholder
        
        return {
            "operations": [],
            "total_operations": 0,
            "message": "Operation history not yet implemented"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get operation history: {str(e)}")


@router.delete("/operations/{operation_id}")
async def cancel_operation(operation_id: str):
    """
    Cancel a specific scraping operation.
    """
    try:
        integration = get_scraper_integration()
        
        if not integration:
            raise HTTPException(status_code=500, detail="Scraper integration not available")
        
        # Check if this is the current operation
        if integration.current_operation_id == operation_id:
            success = await integration.stop_scraping()
            if success:
                return {
                    "success": True,
                    "message": f"Operation {operation_id} cancelled successfully"
                }
            else:
                raise HTTPException(status_code=409, detail="Could not cancel operation")
        else:
            raise HTTPException(status_code=404, detail=f"Operation {operation_id} not found or not active")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel operation: {str(e)}")