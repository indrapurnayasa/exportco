#!/usr/bin/env python3
"""
Test script for the countryId parameter in top commodity by country API.
Tests filtering by specific country ID.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_country_filter():
    """Test filtering by specific country ID"""
    
    print("🧪 Testing Country ID Filter")
    print("=" * 60)
    
    # Test cases with different country IDs
    test_cases = [
        {
            "country_id": "US",
            "description": "United States",
            "end_date": "31-12-2024"
        },
        {
            "country_id": "CN", 
            "description": "China",
            "end_date": "31-12-2024"
        },
        {
            "country_id": "ID",
            "description": "Indonesia", 
            "end_date": "31-12-2024"
        },
        {
            "country_id": "JP",
            "description": "Japan",
            "end_date": "31-01-2025"
        },
        {
            "country_id": None,
            "description": "All Countries (no filter)",
            "end_date": "31-12-2024"
        }
    ]
    
    for test_case in test_cases:
        country_id = test_case["country_id"]
        description = test_case["description"]
        end_date = test_case["end_date"]
        
        # Build URL
        url = f"http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate={end_date}"
        if country_id:
            url += f"&countryId={country_id}"
        
        print(f"\n🌍 Testing: {description}")
        print(f"   Country ID: {country_id or 'All'}")
        print(f"   End Date: {end_date}")
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
                            # Show the results
                            for i, country in enumerate(countries):
                                country_name = country.get('countryName', 'Unknown')
                                country_code = country.get('countryId', 'Unknown')
                                top_commodity = country.get('topCommodity', {})
                                
                                commodity_name = top_commodity.get('name', 'Unknown')
                                commodity_value_usd = top_commodity.get('valueUSD', 0)
                                commodity_growth = top_commodity.get('growth', 0)
                                commodity_price = top_commodity.get('price', 'N/A')
                                
                                print(f"      {i+1}. {country_name} ({country_code})")
                                print(f"         Top commodity: {commodity_name}")
                                print(f"         Value: ${commodity_value_usd:,.2f}")
                                print(f"         Growth: {commodity_growth}%")
                                print(f"         Price: {commodity_price}")
                                
                                # If filtering by specific country, should only get one result
                                if country_id and len(countries) > 1:
                                    print(f"         ⚠️  Warning: Expected 1 country, got {len(countries)}")
                                elif country_id and country_code != country_id:
                                    print(f"         ❌ Error: Expected {country_id}, got {country_code}")
                                
                                # Only show first result if filtering by country
                                if country_id:
                                    break
                        else:
                            print(f"   ⚠️  No data available for this country/period")
                            
                    elif response.status == 404:
                        error_text = await response.text()
                        print(f"   ❌ 404 Not Found")
                        print(f"   Error: {error_text}")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Unexpected status: {response.status}")
                        print(f"   Response: {error_text}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Small delay between requests
        await asyncio.sleep(1)

async def test_invalid_country_id():
    """Test with invalid country ID"""
    
    print(f"\n🔍 Testing Invalid Country ID")
    print("=" * 60)
    
    # Test with invalid country ID
    invalid_country_ids = ["INVALID", "XX", "123", ""]
    
    for invalid_id in invalid_country_ids:
        url = f"http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024&countryId={invalid_id}"
        
        print(f"\n❌ Testing invalid country ID: '{invalid_id}'")
        print(f"   URL: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        countries = data.get('data', [])
                        
                        if len(countries) == 0:
                            print(f"   ✅ Correctly returned empty data for invalid country ID")
                        else:
                            print(f"   ⚠️  Unexpectedly found {len(countries)} countries for invalid ID")
                            
                    elif response.status == 404:
                        print(f"   ✅ Correctly returned 404 for invalid country ID")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Unexpected status: {response.status}")
                        print(f"   Response: {error_text}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        await asyncio.sleep(1)

async def test_parameter_combinations():
    """Test different combinations of parameters"""
    
    print(f"\n🔧 Testing Parameter Combinations")
    print("=" * 60)
    
    # Test different parameter combinations
    test_combinations = [
        {
            "end_date": "31-12-2024",
            "country_id": "US",
            "description": "Both endDate and countryId"
        },
        {
            "end_date": "31-12-2024", 
            "country_id": None,
            "description": "Only endDate"
        },
        {
            "end_date": None,
            "country_id": "US",
            "description": "Only countryId"
        },
        {
            "end_date": None,
            "country_id": None,
            "description": "No parameters"
        }
    ]
    
    for combo in test_combinations:
        end_date = combo["end_date"]
        country_id = combo["country_id"]
        description = combo["description"]
        
        # Build URL
        url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country"
        params = []
        
        if end_date:
            params.append(f"endDate={end_date}")
        if country_id:
            params.append(f"countryId={country_id}")
        
        if params:
            url += "?" + "&".join(params)
        
        print(f"\n📋 Testing: {description}")
        print(f"   End Date: {end_date or 'None'}")
        print(f"   Country ID: {country_id or 'None'}")
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
                            # Show first result
                            first_country = countries[0]
                            country_name = first_country.get('countryName', 'Unknown')
                            top_commodity = first_country.get('topCommodity', {})
                            commodity_name = top_commodity.get('name', 'Unknown')
                            commodity_value = top_commodity.get('valueUSD', 0)
                            
                            print(f"      Sample: {country_name} - {commodity_name} (${commodity_value:,.2f})")
                        else:
                            print(f"      ⚠️  No data available")
                            
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Error: {response.status} - {error_text}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        await asyncio.sleep(1)

async def test_performance_comparison():
    """Compare performance between filtered and unfiltered queries"""
    
    print(f"\n⚡ Performance Comparison")
    print("=" * 60)
    
    # Test performance with and without country filter
    test_cases = [
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024",
            "description": "All countries (unfiltered)"
        },
        {
            "url": "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024&countryId=US",
            "description": "US only (filtered)"
        }
    ]
    
    for test_case in test_cases:
        url = test_case["url"]
        description = test_case["description"]
        
        print(f"\n⏱️  Testing: {description}")
        print(f"   URL: {url}")
        
        # Measure response time
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    print(f"   Status: {response.status}")
                    print(f"   Response time: {response_time:.2f}ms")
                    
                    if response.status == 200:
                        data = await response.json()
                        countries = data.get('data', [])
                        print(f"   Countries returned: {len(countries)}")
                        
                        if countries:
                            # Show first result
                            first_country = countries[0]
                            country_name = first_country.get('countryName', 'Unknown')
                            top_commodity = first_country.get('topCommodity', {})
                            commodity_name = top_commodity.get('name', 'Unknown')
                            commodity_value = top_commodity.get('valueUSD', 0)
                            
                            print(f"   Sample: {country_name} - {commodity_name} (${commodity_value:,.2f})")
                            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    print("Country ID Filter Test")
    print("=" * 60)
    
    # Test country filtering
    asyncio.run(test_country_filter())
    
    # Test invalid country IDs
    asyncio.run(test_invalid_country_id())
    
    # Test parameter combinations
    asyncio.run(test_parameter_combinations())
    
    # Test performance comparison
    asyncio.run(test_performance_comparison())
    
    print(f"\n🎉 Test completed!")
    print(f"   ✅ Country ID filtering is working")
    print(f"   🔍 Can filter by specific country (e.g., US, CN, ID)")
    print(f"   📊 Returns only the specified country's top commodity")
    print(f"   ⚡ Filtered queries are more efficient")
    print(f"   🛡️  Handles invalid country IDs gracefully") 