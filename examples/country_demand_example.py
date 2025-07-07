#!/usr/bin/env python3
"""
Example script demonstrating the country-demand API endpoint.

This script shows how to:
1. Get country demand data for all countries
2. Parse and display the results
"""

import requests
import json
from typing import Dict, Any

# API base URL - adjust this to match your server
BASE_URL = "http://localhost:8000/api/v1"

def get_country_demand() -> Dict[str, Any]:
    """
    Get country demand data from the API.
    
    Returns:
        Dictionary containing the API response
    """
    url = f"{BASE_URL}/export/country-demand"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def display_country_data(country_data: Dict[str, Any]):
    """Display country data in a formatted way"""
    print(f"\n🌍 Country: {country_data['countryName']} ({country_data['countryId']})")
    print(f"📈 Growth Percentage: {country_data['growthPercentage']}%")
    print(f"💰 Current Total Transaction: {country_data['currentTotalTransaction']}")
    
    print(f"\n📦 All Products:")
    for i, product in enumerate(country_data['products'], 1):
        print(f"  {i}. {product['name']} ({product['id']})")
        print(f"     Growth: {product['growth']}%")

def main():
    """Main function to demonstrate the API usage"""
    print("🚀 Country Demand API Example")
    print("=" * 50)
    
    # Get data for all countries
    print("\n1️⃣ Getting data for all countries...")
    all_countries_data = get_country_demand()
    
    if all_countries_data and all_countries_data.get('data'):
        print(f"Found data for {len(all_countries_data['data'])} countries:")
        for country_data in all_countries_data['data']:
            display_country_data(country_data)
    else:
        print("No data found for all countries")
    
    # Show raw JSON response
    print("\n\n2️⃣ Raw JSON Response (first country only):")
    if all_countries_data and all_countries_data.get('data'):
        print(json.dumps(all_countries_data['data'][0], indent=2))
    else:
        print("No data available")

if __name__ == "__main__":
    main() 