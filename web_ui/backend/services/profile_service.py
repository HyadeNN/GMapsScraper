"""
Profile management service.
Handles CRUD operations for scraper configuration profiles.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from api.models.profile import ScrapingProfile, ProfileCreateRequest, ProfileUpdateRequest


class ProfileService:
    """Service for managing scraper configuration profiles."""
    
    def __init__(self, profiles_dir: str = None):
        self.profiles_dir = Path(profiles_dir) if profiles_dir else Path(__file__).parent.parent / "data" / "profiles"
        self.profiles_file = self.profiles_dir / "profiles.json"
        self.ensure_profiles_dir()
    
    def ensure_profiles_dir(self):
        """Ensure profiles directory exists."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def load_profiles(self) -> List[ScrapingProfile]:
        """Load all profiles from storage."""
        if not self.profiles_file.exists():
            return []
        
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ScrapingProfile(**profile) for profile in data.get('profiles', [])]
        except Exception as e:
            print(f"Error loading profiles: {e}")
            return []
    
    def save_profiles(self, profiles: List[ScrapingProfile]):
        """Save profiles to storage."""
        try:
            profiles_data = {
                "profiles": [profile.dict() for profile in profiles],
                "last_updated": datetime.now().isoformat(),
                "version": "2.0.0"
            }
            
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error saving profiles: {e}")
            raise
    
    def get_all_profiles(self) -> List[ScrapingProfile]:
        """Get all profiles."""
        return self.load_profiles()
    
    def get_profile_by_id(self, profile_id: str) -> Optional[ScrapingProfile]:
        """Get a specific profile by ID."""
        profiles = self.load_profiles()
        return next((p for p in profiles if p.id == profile_id), None)
    
    def get_default_profile(self) -> Optional[ScrapingProfile]:
        """Get the default profile."""
        profiles = self.load_profiles()
        return next((p for p in profiles if p.is_default), None)
    
    def create_profile(self, profile_request: ProfileCreateRequest) -> ScrapingProfile:
        """Create a new profile."""
        profiles = self.load_profiles()
        
        # Check for duplicate names
        if any(p.name == profile_request.name for p in profiles):
            raise ValueError(f"Profile with name '{profile_request.name}' already exists")
        
        # If this is set as default, unset other defaults
        if profile_request.is_default:
            for profile in profiles:
                profile.is_default = False
        
        # Create new profile
        new_profile = ScrapingProfile(
            name=profile_request.name,
            description=profile_request.description,
            settings=profile_request.settings,
            locations=profile_request.locations,
            is_default=profile_request.is_default,
            tags=profile_request.tags
        )
        
        profiles.append(new_profile)
        self.save_profiles(profiles)
        
        return new_profile
    
    def update_profile(self, profile_id: str, update_request: ProfileUpdateRequest) -> Optional[ScrapingProfile]:
        """Update an existing profile."""
        profiles = self.load_profiles()
        profile_index = next((i for i, p in enumerate(profiles) if p.id == profile_id), None)
        
        if profile_index is None:
            return None
        
        profile = profiles[profile_index]
        
        # Update fields if provided
        if update_request.name is not None:
            # Check for name conflicts
            if any(p.name == update_request.name and p.id != profile_id for p in profiles):
                raise ValueError(f"Profile with name '{update_request.name}' already exists")
            profile.name = update_request.name
        
        if update_request.description is not None:
            profile.description = update_request.description
        
        if update_request.settings is not None:
            profile.settings = update_request.settings
        
        if update_request.locations is not None:
            profile.locations = update_request.locations
        
        if update_request.tags is not None:
            profile.tags = update_request.tags
        
        if update_request.is_default is not None:
            if update_request.is_default:
                # Unset other defaults
                for p in profiles:
                    p.is_default = False
            profile.is_default = update_request.is_default
        
        self.save_profiles(profiles)
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        profiles = self.load_profiles()
        profile_index = next((i for i, p in enumerate(profiles) if p.id == profile_id), None)
        
        if profile_index is None:
            return False
        
        profiles.pop(profile_index)
        self.save_profiles(profiles)
        return True
    
    def duplicate_profile(self, profile_id: str, new_name: Optional[str] = None) -> Optional[ScrapingProfile]:
        """Create a duplicate of an existing profile."""
        original_profile = self.get_profile_by_id(profile_id)
        if not original_profile:
            return None
        
        profiles = self.load_profiles()
        
        # Generate new name
        duplicate_name = new_name or f"{original_profile.name} (Copy)"
        counter = 1
        original_duplicate_name = duplicate_name
        while any(p.name == duplicate_name for p in profiles):
            duplicate_name = f"{original_duplicate_name} ({counter})"
            counter += 1
        
        # Create duplicate
        duplicate_profile = ScrapingProfile(
            name=duplicate_name,
            description=f"Copy of: {original_profile.description}" if original_profile.description else None,
            settings=original_profile.settings,
            locations=original_profile.locations,
            is_default=False,  # Never set copy as default
            tags=original_profile.tags.copy() if original_profile.tags else []
        )
        
        profiles.append(duplicate_profile)
        self.save_profiles(profiles)
        
        return duplicate_profile
    
    def set_default_profile(self, profile_id: str) -> bool:
        """Set a profile as the default."""
        profiles = self.load_profiles()
        target_profile = next((p for p in profiles if p.id == profile_id), None)
        
        if not target_profile:
            return False
        
        # Unset all defaults
        for profile in profiles:
            profile.is_default = False
        
        # Set target as default
        target_profile.is_default = True
        
        self.save_profiles(profiles)
        return True
    
    def update_profile_usage(self, profile_id: str) -> bool:
        """Update profile usage statistics."""
        profiles = self.load_profiles()
        profile = next((p for p in profiles if p.id == profile_id), None)
        
        if not profile:
            return False
        
        profile.last_used = datetime.now()
        profile.usage_count += 1
        
        self.save_profiles(profiles)
        return True
    
    def search_profiles(self, query: str = None, tags: List[str] = None) -> List[ScrapingProfile]:
        """Search profiles by name, description, or tags."""
        profiles = self.load_profiles()
        
        if not query and not tags:
            return profiles
        
        filtered_profiles = []
        
        for profile in profiles:
            matches = True
            
            # Text search
            if query:
                query_lower = query.lower()
                text_match = (
                    query_lower in profile.name.lower() or
                    (profile.description and query_lower in profile.description.lower())
                )
                if not text_match:
                    matches = False
            
            # Tag filter
            if tags and matches:
                tag_match = any(tag in profile.tags for tag in tags)
                if not tag_match:
                    matches = False
            
            if matches:
                filtered_profiles.append(profile)
        
        return filtered_profiles
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get statistics about profiles."""
        profiles = self.load_profiles()
        
        if not profiles:
            return {
                "total_profiles": 0,
                "most_used_profile": None,
                "recent_profiles": [],
                "profiles_by_category": {},
                "default_profile": None
            }
        
        # Most used profile
        most_used = max(profiles, key=lambda p: p.usage_count) if profiles else None
        
        # Recent profiles (by last_used)
        recent_profiles = sorted(
            [p for p in profiles if p.last_used], 
            key=lambda p: p.last_used,
            reverse=True
        )[:5]
        
        # Profiles by category (tags)
        profiles_by_category = {}
        for profile in profiles:
            for tag in profile.tags:
                profiles_by_category[tag] = profiles_by_category.get(tag, 0) + 1
        
        # Default profile
        default_profile = next((p for p in profiles if p.is_default), None)
        
        return {
            "total_profiles": len(profiles),
            "most_used_profile": most_used.name if most_used else None,
            "recent_profiles": [p.name for p in recent_profiles],
            "profiles_by_category": profiles_by_category,
            "default_profile": default_profile.name if default_profile else None
        }
    
    def export_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Export a profile to a dictionary."""
        profile = self.get_profile_by_id(profile_id)
        if not profile:
            return None
        
        return {
            "export_version": "2.0.0",
            "exported_at": datetime.now().isoformat(),
            "profile": profile.dict()
        }
    
    def import_profile(self, profile_data: Dict[str, Any], overwrite_existing: bool = False) -> ScrapingProfile:
        """Import a profile from dictionary data."""
        profiles = self.load_profiles()
        
        # Extract profile from import data
        if "profile" in profile_data:
            imported_profile_data = profile_data["profile"]
        else:
            imported_profile_data = profile_data
        
        # Create profile object
        imported_profile = ScrapingProfile(**imported_profile_data)
        
        # Check for name conflicts
        existing_profile = next((p for p in profiles if p.name == imported_profile.name), None)
        
        if existing_profile and not overwrite_existing:
            # Generate new name
            original_name = imported_profile.name
            counter = 1
            while any(p.name == imported_profile.name for p in profiles):
                imported_profile.name = f"{original_name} (Imported {counter})"
                counter += 1
        elif existing_profile and overwrite_existing:
            # Remove existing profile
            profiles = [p for p in profiles if p.name != imported_profile.name]
        
        # Reset some fields for imported profile
        imported_profile.id = None  # Will generate new ID
        imported_profile.created_at = datetime.now()
        imported_profile.last_used = None
        imported_profile.is_default = False
        imported_profile.usage_count = 0
        
        profiles.append(imported_profile)
        self.save_profiles(profiles)
        
        return imported_profile
    
    def backup_profiles(self) -> Dict[str, Any]:
        """Create a backup of all profiles."""
        profiles = self.load_profiles()
        
        return {
            "backup_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "created_at": datetime.now().isoformat(),
            "profiles": [profile.dict() for profile in profiles],
            "version": "2.0.0",
            "total_profiles": len(profiles)
        }
    
    def restore_profiles(self, backup_data: Dict[str, Any], merge: bool = False) -> int:
        """Restore profiles from backup data."""
        if not merge:
            # Replace all profiles
            profiles = [ScrapingProfile(**profile_data) for profile_data in backup_data.get("profiles", [])]
        else:
            # Merge with existing profiles
            existing_profiles = self.load_profiles()
            backup_profiles = [ScrapingProfile(**profile_data) for profile_data in backup_data.get("profiles", [])]
            
            # Create a dictionary of existing profiles by name
            existing_by_name = {p.name: p for p in existing_profiles}
            
            # Merge profiles
            profiles = list(existing_profiles)
            for backup_profile in backup_profiles:
                if backup_profile.name not in existing_by_name:
                    profiles.append(backup_profile)
        
        self.save_profiles(profiles)
        return len(profiles)