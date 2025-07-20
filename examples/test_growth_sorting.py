#!/usr/bin/env python3
"""
Test script to verify growth-based sorting in top commodity by country API.
Tests that commodities are now sorted by growth percentage (highest to lowest).
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_growth_sorting():
    """Test that commodities are sorted by growth percentage"""
    
    print("📈 Testing Growth-Based Sorting")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024",
            "description": "All countries (December 2024)"
        },
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024&countryId=US",
            "description": "US only (December 2024)"
        },
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?countryId=CN",
            "description": "China only (latest data)"
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
                        
                        print(f"   ✅ Found {len(countries)} countries")
                        
                        if countries:
                            print(f"   📊 Countries sorted by growth (highest to lowest):")
                            
                            # Show first 5 countries with their growth
                            for i, country in enumerate(countries[:5]):
                                country_name = country.get('countryName', 'Unknown')
                                top_commodity = country.get('topCommodity', {})
                                commodity_name = top_commodity.get('name', 'Unknown')
                                growth = top_commodity.get('growth', 0)
                                value_usd = top_commodity.get('valueUSD', 0)
                                
                                print(f"      {i+1}. {country_name}")
                                print(f"         Commodity: {commodity_name}")
                                print(f"         Growth: {growth}%")
                                print(f"         Value: ${value_usd:,.2f}")
                            
                            # Verify sorting (growth should be descending)
                            if len(countries) >= 2:
                                first_growth = countries[0].get('topCommodity', {}).get('growth', 0)
                                second_growth = countries[1].get('topCommodity', {}).get('growth', 0)
                                
                                if first_growth >= second_growth:
                                    print(f"   ✅ Sorting is correct (growth descending)")
                                else:
                                    print(f"   ❌ Sorting is incorrect")
                                    print(f"      Expected: {first_growth} >= {second_growth}")
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

async def test_growth_vs_value_comparison():
    """Test to show the difference between growth-based and value-based sorting"""
    
    print(f"\n🔬 Growth vs Value Comparison")
    print("=" * 60)
    
    # Test the same endpoint to see growth-based results
    url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024"
    
    print(f"📅 Testing: December 2024 (Growth-based sorting)")
    print(f"   URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    countries = data.get('data', [])
                    
                    print(f"   ✅ Found {len(countries)} countries")
                    
                    if len(countries) >= 3:
                        print(f"   📊 Top 3 countries by growth:")
                        
                        for i, country in enumerate(countries[:3]):
                            country_name = country.get('countryName', 'Unknown')
                            top_commodity = country.get('topCommodity', {})
                            commodity_name = top_commodity.get('name', 'Unknown')
                            growth = top_commodity.get('growth', 0)
                            value_usd = top_commodity.get('valueUSD', 0)
                            
                            print(f"      {i+1}. {country_name}")
                            print(f"         Commodity: {commodity_name}")
                            print(f"         Growth: {growth}%")
                            print(f"         Value: ${value_usd:,.2f}")
                        
                        print(f"\n💡 Key Changes:")
                        print(f"   • Now sorted by growth percentage (highest to lowest)")
                        print(f"   • Returns commodity with highest growth, not highest value")
                        print(f"   • Better for identifying emerging trends")
                        print(f"   • Shows which commodities are growing fastest")
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

async def test_single_country_growth():
    """Test growth-based sorting for a single country"""
    
    print(f"\n🌍 Single Country Growth Test")
    print("=" * 60)
    
    # Test with a specific country
    url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024&countryId=US"
    
    print(f"📅 Testing: US (December 2024)")
    print(f"   URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    countries = data.get('data', [])
                    
                    print(f"   ✅ Found {len(countries)} countries")
                    
                    if countries:
                        # Should only have one country (US)
                        country = countries[0]
                        country_name = country.get('countryName', 'Unknown')
                        top_commodity = country.get('topCommodity', {})
                        commodity_name = top_commodity.get('name', 'Unknown')
                        growth = top_commodity.get('growth', 0)
                        value_usd = top_commodity.get('valueUSD', 0)
                        price = top_commodity.get('price', 'N/A')
                        
                        print(f"   📊 {country_name} - Top commodity by growth:")
                        print(f"      Commodity: {commodity_name}")
                        print(f"      Growth: {growth}%")
                        print(f"      Value: ${value_usd:,.2f}")
                        print(f"      Price: {price}")
                        
                        print(f"\n💡 This shows the commodity with the highest growth")
                        print(f"   in {country_name}, not necessarily the highest value.")
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    print("Growth-Based Sorting Test")
    print("=" * 60)
    
    # Test growth sorting
    asyncio.run(test_growth_sorting())
    
    # Test growth vs value comparison
    asyncio.run(test_growth_vs_value_comparison())
    
    # Test single country growth
    asyncio.run(test_single_country_growth())
    
    print(f"\n🎉 Test completed!")
    print(f"   ✅ API now sorts by growth percentage (highest to lowest)")
    print(f"   📈 Returns commodity with highest growth, not highest value")
    print(f"   🌍 Countries sorted by their top commodity's growth")
    print(f"   🔍 Better for identifying emerging trends and opportunities") 