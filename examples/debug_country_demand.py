#!/usr/bin/env python3
"""
Debug script to test country demand endpoint and identify the 404 error.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def debug_country_demand():
    """Debug the country demand endpoint"""
    
    # Test different scenarios
    test_cases = [
        {"url": "http://0.0.0.0:8000/api/v1/export/country-demand", "description": "No date parameter"},
        {"url": "http://0.0.0.0:8000/api/v1/export/country-demand?endDate=31-12-2024", "description": "Q4 2024"},
        {"url": "http://0.0.0.0:8000/api/v1/export/country-demand?endDate=31-03-2025", "description": "Q1 2025"},
        {"url": "http://0.0.0.0:8000/api/v1/export/country-demand?endDate=30-06-2025", "description": "Q2 2025"},
        {"url": "http://0.0.0.0:8000/api/v1/export/country-demand?endDate=30-09-2025", "description": "Q3 2025"},
    ]
    
    print("🔍 Debugging Country Demand Endpoint")
    print("=" * 60)
    
    for test_case in test_cases:
        url = test_case["url"]
        description = test_case["description"]
        
        print(f"\n📅 Testing: {description}")
        print(f"   URL: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        countries = data.get('data', [])
                        print(f"   ✅ Success! Found {len(countries)} countries")
                        
                        if countries:
                            # Show first country details
                            first_country = countries[0]
                            print(f"   📊 First country: {first_country.get('countryName', 'Unknown')}")
                            print(f"      Growth: {first_country.get('growthPercentage', 0)}%")
                            print(f"      Products: {len(first_country.get('products', []))}")
                            
                            # Show first few products (should be sorted by growth)
                            if first_country.get('products'):
                                print(f"      Products (sorted by growth):")
                                for i, product in enumerate(first_country['products'][:3]):  # Show first 3 products
                                    print(f"         {i+1}. {product.get('name', 'Unknown')}: {product.get('growth', 0)}% - {product.get('price', 'N/A')}")
                        else:
                            print(f"   ⚠️  No data available for this quarter (this is normal)")
                            
                    elif response.status == 404:
                        error_text = await response.text()
                        print(f"   ❌ 404 Not Found")
                        print(f"   Error: {error_text}")
                        
                    elif response.status == 500:
                        error_text = await response.text()
                        print(f"   ❌ 500 Internal Server Error")
                        print(f"   Error: {error_text}")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Unexpected status: {response.status}")
                        print(f"   Response: {error_text}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    print(f"\n🎯 Debug Summary:")
    print("=" * 60)
    print("If you see 404 errors, it might be because:")
    print("1. No data exists for the specified quarter")
    print("2. Date parsing is failing")
    print("3. Database queries are returning empty results")
    print("\nCheck the server logs for debug messages to identify the issue.")

if __name__ == "__main__":
    asyncio.run(debug_country_demand()) 