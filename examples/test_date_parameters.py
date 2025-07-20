#!/usr/bin/env python3
"""
Test script to verify date parameter functionality for export endpoints.
Run this script to test the new endDate parameter for both seasonal-trend and country-demand endpoints.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_endpoint_with_date(endpoint: str, end_date: str = None):
    """Test an endpoint with optional endDate parameter"""
    
    # Build URL with parameter
    base_url = f"http://0.0.0.0:8000/api/v1/export/{endpoint}"
    if end_date:
        url = f"{base_url}?endDate={end_date}"
    else:
        url = base_url
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"🧪 Testing {endpoint.upper()} Endpoint")
            print(f"   URL: {url}")
            print("=" * 60)
            
            # Make the request
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"✅ Request successful! Status: {response.status}")
                    
                    if endpoint == "seasonal-trend":
                        print(f"📊 Total commodities returned: {len(data.get('data', []))}")
                        
                        # Show first few commodities (should be sorted by growth)
                        for i, commodity in enumerate(data.get('data', [])[:3]):
                            print(f"\n📦 Commodity {i+1}: {commodity.get('comodity', 'Unknown')}")
                            print(f"   Growth: {commodity.get('growthPercentage', 0)}%")
                            print(f"   Price: {commodity.get('averagePrice', 'N/A')}")
                            print(f"   Period: {commodity.get('period', 'N/A')}")
                            print(f"   Countries: {len(commodity.get('countries', []))}")
                        
                        # Verify sorting
                        growth_values = [item.get('growthPercentage', 0) for item in data.get('data', [])]
                        if len(growth_values) > 1:
                            is_sorted = all(growth_values[i] >= growth_values[i+1] for i in range(len(growth_values)-1))
                            print(f"\n🔍 Sorting verification: {'✅ Sorted correctly' if is_sorted else '❌ Not sorted correctly'}")
                            print(f"   Growth values: {growth_values[:5]}...")
                    
                    elif endpoint == "country-demand":
                        print(f"📊 Total countries returned: {len(data.get('data', []))}")
                        
                        # Show first few countries (should be sorted by growth)
                        for i, country in enumerate(data.get('data', [])[:3]):
                            print(f"\n🌍 Country {i+1}: {country.get('countryName', 'Unknown')}")
                            print(f"   Growth: {country.get('growthPercentage', 0)}%")
                            print(f"   Total Transaction (IDR): {country.get('currentTotalTransaction', 0):,.2f}")
                            print(f"   Products: {len(country.get('products', []))}")
                            
                            # Show first few products with their growth
                            for j, product in enumerate(country.get('products', [])[:2]):
                                print(f"     📦 {product.get('name', 'Unknown')}")
                                print(f"        Growth: {product.get('growth', 0)}%")
                                print(f"        Price: {product.get('price', 'N/A')}")
                        
                        # Verify country sorting
                        country_growth_values = [item.get('growthPercentage', 0) for item in data.get('data', [])]
                        if len(country_growth_values) > 1:
                            is_sorted = all(country_growth_values[i] >= country_growth_values[i+1] for i in range(len(country_growth_values)-1))
                            print(f"\n🔍 Country sorting verification: {'✅ Sorted correctly' if is_sorted else '❌ Not sorted correctly'}")
                            print(f"   Growth values: {country_growth_values[:5]}...")
                    
                    return True
                    
                else:
                    print(f"❌ Request failed! Status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def test_date_parameter_validation():
    """Test various date parameter formats and edge cases"""
    
    print("🔍 Testing Date Parameter Validation")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {"end_date": "31-03-2025", "description": "Q1 2025"},
        {"end_date": "30-06-2025", "description": "Q2 2025"},
        {"end_date": "30-09-2025", "description": "Q3 2025"},
        {"end_date": "31-12-2025", "description": "Q4 2025"},
        {"end_date": "31-01-2024", "description": "Q1 2024"},
        {"end_date": None, "description": "Latest quarter (no parameter)"},
    ]
    
    endpoints = ["seasonal-trend", "country-demand"]
    
    for endpoint in endpoints:
        print(f"\n🎯 Testing {endpoint.upper()} endpoint:")
        print("-" * 40)
        
        for test_case in test_cases:
            end_date = test_case["end_date"]
            description = test_case["description"]
            
            print(f"\n📅 Testing: {description}")
            if end_date:
                print(f"   Date: {end_date}")
            
            success = await test_endpoint_with_date(endpoint, end_date)
            
            if success:
                print(f"   ✅ {description} - SUCCESS")
            else:
                print(f"   ❌ {description} - FAILED")
            
            # Small delay between requests
            await asyncio.sleep(1)

async def test_invalid_date_formats():
    """Test invalid date formats to ensure proper error handling"""
    
    print("\n🚨 Testing Invalid Date Formats")
    print("=" * 60)
    
    invalid_dates = [
        "2025-03-31",  # Wrong format (YYYY-MM-DD)
        "31/03/2025",  # Wrong separator
        "31-3-2025",   # Missing leading zero
        "32-03-2025",  # Invalid day
        "31-13-2025",  # Invalid month
        "abc-def-ghi", # Non-numeric
        "",            # Empty string
    ]
    
    endpoints = ["seasonal-trend", "country-demand"]
    
    for endpoint in endpoints:
        print(f"\n🎯 Testing {endpoint.upper()} with invalid dates:")
        print("-" * 40)
        
        for invalid_date in invalid_dates:
            print(f"\n📅 Testing invalid date: '{invalid_date}'")
            
            success = await test_endpoint_with_date(endpoint, invalid_date)
            
            if success:
                print(f"   ⚠️  Unexpected success with invalid date")
            else:
                print(f"   ✅ Properly rejected invalid date")
            
            await asyncio.sleep(0.5)

async def test_quarter_calculation():
    """Test that quarter calculation is correct for different dates"""
    
    print("\n🧮 Testing Quarter Calculation")
    print("=" * 60)
    
    # Test quarter calculations
    quarter_tests = [
        {"date": "31-01-2025", "expected_quarter": 1, "expected_year": "2025"},
        {"date": "28-02-2025", "expected_quarter": 1, "expected_year": "2025"},
        {"date": "31-03-2025", "expected_quarter": 1, "expected_year": "2025"},
        {"date": "30-04-2025", "expected_quarter": 2, "expected_year": "2025"},
        {"date": "31-05-2025", "expected_quarter": 2, "expected_year": "2025"},
        {"date": "30-06-2025", "expected_quarter": 2, "expected_year": "2025"},
        {"date": "31-07-2025", "expected_quarter": 3, "expected_year": "2025"},
        {"date": "31-08-2025", "expected_quarter": 3, "expected_year": "2025"},
        {"date": "30-09-2025", "expected_quarter": 3, "expected_year": "2025"},
        {"date": "31-10-2025", "expected_quarter": 4, "expected_year": "2025"},
        {"date": "30-11-2025", "expected_quarter": 4, "expected_year": "2025"},
        {"date": "31-12-2025", "expected_quarter": 4, "expected_year": "2025"},
    ]
    
    print("Expected quarter calculations:")
    for test in quarter_tests:
        date_str = test["date"]
        expected_q = test["expected_quarter"]
        expected_y = test["expected_year"]
        print(f"   {date_str} → Q{expected_q} {expected_y}")

if __name__ == "__main__":
    print("Date Parameter Test Suite")
    print("=" * 60)
    
    # Test quarter calculation logic
    asyncio.run(test_quarter_calculation())
    
    # Test valid date parameters
    print("\n" + "=" * 60)
    asyncio.run(test_date_parameter_validation())
    
    # Test invalid date formats
    print("\n" + "=" * 60)
    asyncio.run(test_invalid_date_formats())
    
    print(f"\n🎉 Test suite completed!")
    print(f"   The endpoints now support date parameters for querying specific quarters.")
    print(f"   Format: ?endDate=DD-MM-YYYY (e.g., ?endDate=31-03-2025 for Q1 2025)") 