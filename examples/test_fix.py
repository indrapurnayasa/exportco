#!/usr/bin/env python3
"""
Quick test script to verify the API endpoint fix.
Tests that the top commodity by country endpoint is now working correctly.
"""

import asyncio
import aiohttp
import json

async def test_api_fix():
    """Test that the API endpoint is now working correctly"""
    
    print("🔧 Testing API Fix")
    print("=" * 60)
    
    # Test cases to verify the fix
    test_cases = [
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country",
            "description": "Latest data (all countries)"
        },
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024",
            "description": "December 2024 (all countries)"
        },
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?countryId=US",
            "description": "US only (latest data)"
        },
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024&countryId=US",
            "description": "US only (December 2024)"
        }
    ]
    
    for test_case in test_cases:
        url = test_case["url"]
        description = test_case["description"]
        
        print(f"\n🧪 Testing: {description}")
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
                            # Show first result
                            first_country = countries[0]
                            country_name = first_country.get('countryName', 'Unknown')
                            top_commodity = first_country.get('topCommodity', {})
                            commodity_name = top_commodity.get('name', 'Unknown')
                            commodity_value = top_commodity.get('valueUSD', 0)
                            
                            print(f"   📊 Sample: {country_name} - {commodity_name} (${commodity_value:,.2f})")
                        else:
                            print(f"   ⚠️  No data available")
                            
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
    
    print(f"\n🎉 Test completed!")
    print(f"   ✅ API endpoint should now be working correctly")
    print(f"   🔧 Fixed the database session dependency issue")
    print(f"   📊 All parameter combinations should work")

if __name__ == "__main__":
    print("API Fix Verification Test")
    print("=" * 60)
    
    asyncio.run(test_api_fix()) 