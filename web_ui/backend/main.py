"""
FastAPI main application for Google Maps Scraper Web UI.
This serves as the backend API for the React frontend.
"""

import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

# Add the parent directory to Python path to import gmaps_scraper
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir.parent.parent))

from api.routes import locations, scraper, profiles, settings, websocket
from utils.integration import ScraperIntegration
from services.profile_service import ProfileService
from services.location_service import LocationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting Google Maps Scraper Web UI Backend...")
    
    # Initialize services
    app.state.scraper_integration = ScraperIntegration()
    app.state.profile_service = ProfileService()
    app.state.location_service = LocationService()
    
    # Load location data
    await app.state.scraper_integration.load_locations()
    
    print("✅ Backend startup complete!")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down backend...")
    
    # Cleanup any running scraper tasks
    if hasattr(app.state, 'scraper_integration'):
        await app.state.scraper_integration.cleanup()
    
    print("✅ Backend shutdown complete!")


# Create FastAPI application
app = FastAPI(
    title="Google Maps Scraper API",
    description="Web API for controlling and monitoring Google Maps scraping operations",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite development server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection function
def get_scraper_integration():
    return app.state.scraper_integration

def get_profile_service():
    return app.state.profile_service

def get_location_service():
    return app.state.location_service

# Set dependencies in route modules
from api.routes import locations, scraper, profiles, settings, websocket
locations.get_scraper_integration = get_scraper_integration
locations.get_location_service = get_location_service
scraper.get_scraper_integration = get_scraper_integration
profiles.get_profile_service = get_profile_service
settings.get_scraper_integration = get_scraper_integration
websocket.get_scraper_integration = get_scraper_integration

# Include API routers
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["profiles"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Google Maps Scraper API is running",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Google Maps Scraper Web API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["./"],
        log_level="info"
    )