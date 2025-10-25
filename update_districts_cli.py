#!/usr/bin/env python3
"""
Command-line version of district updater for systems with GUI issues
"""

import os
import sys
import json
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from gmaps_scraper.utils.logger import logger


class DistrictUpdaterCLI:
    def __init__(self):
        self.district_pattern = re.compile(
            r'(?:^|\s)([A-ZÇĞIİÖŞÜ][a-zçğıiöşü]+(?:\s[A-ZÇĞIİÖŞÜ][a-zçğıiöşü]+)*)\s*(?:Mah\.|Mahallesi|İlçesi|ilçesi)',
            re.UNICODE
        )
        
    def extract_district_from_address(self, address: str) -> str:
        """Extract district name from a Turkish address."""
        if not address or pd.isna(address):
            return ""
            
        # Clean the address
        address = str(address).strip()
        
        # Search for district patterns
        match = self.district_pattern.search(address)
        if match:
            return match.group(1).strip()
            
        # Fallback: look for common Istanbul districts
        istanbul_districts = [
            "Kadıköy", "Beşiktaş", "Şişli", "Bakırköy", "Üsküdar",
            "Ataşehir", "Maltepe", "Kartal", "Pendik", "Tuzla",
            "Ümraniye", "Çekmeköy", "Sancaktepe", "Sultanbeyli",
            "Fatih", "Beyoğlu", "Zeytinburnu", "Bayrampaşa", "Eyüpsultan",
            "Gaziosmanpaşa", "Esenler", "Güngören", "Bağcılar",
            "Bahçelievler", "Küçükçekmece", "Başakşehir", "Avcılar",
            "Beylikdüzü", "Esenyurt", "Büyükçekmece", "Çatalca",
            "Silivri", "Sultangazi", "Arnavutköy", "Sancaktepe",
            "Sarıyer", "Kağıthane", "Beykoz", "Adalar"
        ]
        
        for district in istanbul_districts:
            if district in address:
                return district
                
        return ""
    
    def process_excel_file(self, input_file: str, output_folder: str) -> Dict[str, List[str]]:
        """Process Excel file and extract districts."""
        logger.info(f"Processing {input_file}")
        
        # Read Excel file
        df = pd.read_excel(input_file)
        logger.info(f"Loaded {len(df)} records from Excel")
        
        # Look for address columns
        address_columns = [col for col in df.columns if 'address' in col.lower() or 'adres' in col.lower()]
        
        if not address_columns:
            logger.warning("No address columns found in Excel file")
            return {}
            
        # Extract districts
        districts_by_city = {}
        
        for col in address_columns:
            logger.info(f"Processing column: {col}")
            
            for idx, address in enumerate(df[col]):
                if pd.notna(address):
                    district = self.extract_district_from_address(address)
                    if district:
                        # For now, assume all are in Istanbul
                        city = "İstanbul"
                        if city not in districts_by_city:
                            districts_by_city[city] = set()
                        districts_by_city[city].add(district)
                        
                        if idx % 100 == 0:
                            logger.info(f"Processed {idx}/{len(df)} addresses")
        
        # Convert sets to lists
        for city in districts_by_city:
            districts_by_city[city] = sorted(list(districts_by_city[city]))
            logger.info(f"Found {len(districts_by_city[city])} unique districts in {city}")
            
        return districts_by_city
    
    def update_locations_file(self, districts_by_city: Dict[str, List[str]], output_folder: str):
        """Update locations.json with new districts."""
        locations_file = Path(output_folder) / "locations.json"
        
        # Load existing locations
        if locations_file.exists():
            with open(locations_file, 'r', encoding='utf-8') as f:
                locations = json.load(f)
        else:
            locations = {"cities": {}}
            
        # Update with new districts
        updated_count = 0
        
        for city, new_districts in districts_by_city.items():
            if city not in locations["cities"]:
                locations["cities"][city] = {"districts": {}}
                
            existing_districts = set(locations["cities"][city].get("districts", {}).keys())
            
            for district in new_districts:
                if district not in existing_districts:
                    locations["cities"][city]["districts"][district] = {
                        "lat": None,
                        "lng": None,
                        "location_count": 0
                    }
                    updated_count += 1
                    logger.info(f"Added new district: {city} - {district}")
        
        # Save updated locations
        if updated_count > 0:
            with open(locations_file, 'w', encoding='utf-8') as f:
                json.dump(locations, f, ensure_ascii=False, indent=2)
            logger.info(f"Updated locations.json with {updated_count} new districts")
        else:
            logger.info("No new districts found to add")
            
        return updated_count


def main():
    parser = argparse.ArgumentParser(description='Update districts from Excel file')
    parser.add_argument('input_excel', help='Path to input Excel file')
    parser.add_argument('-o', '--output', default='.', help='Output folder (default: current directory)')
    
    args = parser.parse_args()
    
    if not Path(args.input_excel).exists():
        logger.error(f"Input file not found: {args.input_excel}")
        sys.exit(1)
        
    updater = DistrictUpdaterCLI()
    
    try:
        # Process Excel file
        districts = updater.process_excel_file(args.input_excel, args.output)
        
        if districts:
            # Update locations file
            updated = updater.update_locations_file(districts, args.output)
            logger.info(f"\nProcess completed! Added {updated} new districts.")
        else:
            logger.warning("No districts found in the Excel file")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()