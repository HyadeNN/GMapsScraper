#!/usr/bin/env python3
"""Test script for the new Google Places API implementation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gmaps_scraper.core.scraper import GooglePlacesScraper
from gmaps_scraper.core.data_processor import DataProcessor
from gmaps_scraper.config.settings import API_KEY
import json

def test_new_api():
    """Test the new Places API implementation with a simple search."""
    
    print("Testing Google Places API (New) implementation...")
    print("=" * 50)
    
    # Initialize scraper
    try:
        scraper = GooglePlacesScraper(api_key=API_KEY)
        print("✓ Scraper initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize scraper: {e}")
        return
    
    # Test location - Kadıköy, Istanbul
    test_location = (40.9911, 29.0367)
    test_keyword = "diş kliniği"
    test_radius = 2000  # 2km radius
    
    print(f"\nTesting search for '{test_keyword}' near Kadıköy, Istanbul")
    print(f"Location: {test_location}")
    print(f"Radius: {test_radius}m")
    print("-" * 50)
    
    try:
        # Test search_places method
        results = scraper.search_places(
            keyword=test_keyword,
            location=test_location,
            radius=test_radius
        )
        
        print(f"\n✓ Search completed. Found {len(results)} places")
        
        if results:
            # Show first result
            print("\nFirst result (raw API response):")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
            
            # Test format conversion
            print("\n" + "-" * 50)
            print("Testing format conversion...")
            converted = scraper._convert_new_api_format(results[0])
            print("\nConverted format:")
            print(json.dumps(converted, indent=2, ensure_ascii=False))
            
            # Test data processor
            print("\n" + "-" * 50)
            print("Testing data processor...")
            processor = DataProcessor()
            processed = processor.extract_place_data(
                converted, 
                search_term=test_keyword,
                city="İstanbul",
                district="Kadıköy"
            )
            
            if processed:
                print("\n✓ Data processing successful")
                print("\nProcessed data:")
                print(json.dumps(processed, indent=2, ensure_ascii=False))
            else:
                print("\n✗ Data processing failed")
        
    except Exception as e:
        print(f"\n✗ Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_api()