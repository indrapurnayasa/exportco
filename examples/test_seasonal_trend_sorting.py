#!/usr/bin/env python3
"""
Test script to verify seasonal trend sorting by growth percentage.
Run this script to test that commodities are sorted from highest to lowest growth.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any

async def test_seasonal_trend_sorting(end_date: str = None):
    """Test that seasonal trend results are sorted by growth percentage"""
    
    # Build URL
    base_url = "http://0.0.0.0:8000/api/v1/export/seasonal-trend"
    if end_date:
        url = f"{base_url}?endDate={end_date}"
    else:
        url = base_url
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"🧪 Testing Seasonal Trend Sorting")
            print(f"   URL: {url}")
            print("=" * 60)
            
            # Make the request
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    commodities = data.get('data', [])
                    
                    print(f"✅ Request successful! Status: {response.status}")
                    print(f"📊 Total commodities returned: {len(commodities)}")
                    
                    if len(commodities) == 0:
                        print("⚠️  No commodities returned")
                        return True
                    
                    # Extract growth percentages
                    growth_values = [item.get('growthPercentage', 0) for item in commodities]
                    
                    # Check if sorted correctly (highest to lowest)
                    is_sorted = all(growth_values[i] >= growth_values[i+1] for i in range(len(growth_values)-1))
                    
                    print(f"\n🔍 Sorting Analysis:")
                    print(f"   Expected: Highest to lowest growth")
                    print(f"   Actual: {'✅ Sorted correctly' if is_sorted else '❌ Not sorted correctly'}")
                    
                    # Show top 10 commodities with their growth
                    print(f"\n📈 Top 10 Commodities by Growth:")
                    print("-" * 50)
                    for i, commodity in enumerate(commodities[:10]):
                        name = commodity.get('comodity', 'Unknown')
                        growth = commodity.get('growthPercentage', 0)
                        price = commodity.get('averagePrice', 'N/A')
                        countries = len(commodity.get('countries', []))
                        
                        print(f"{i+1:2d}. {name[:40]:<40} {growth:>8.2f}%  {price:>12}  {countries} countries")
                    
                    # Show growth values for verification
                    print(f"\n📊 Growth Values (first 10):")
                    print(f"   {growth_values[:10]}")
                    
                    # Check for any anomalies
                    if len(growth_values) > 1:
                        max_growth = max(growth_values)
                        min_growth = min(growth_values)
                        print(f"\n📊 Growth Range:")
                        print(f"   Highest: {max_growth:.2f}%")
                        print(f"   Lowest: {min_growth:.2f}%")
                        print(f"   Range: {max_growth - min_growth:.2f}%")
                    
                    return is_sorted
                    
                else:
                    print(f"❌ Request failed! Status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def test_multiple_quarters():
    """Test sorting across multiple quarters"""
    
    print("🔄 Testing Multiple Quarters")
    print("=" * 60)
    
    # Test different quarters
    test_cases = [
        {"end_date": "31-03-2025", "description": "Q1 2025"},
        {"end_date": "30-06-2025", "description": "Q2 2025"},
        {"end_date": "30-09-2025", "description": "Q3 2025"},
        {"end_date": "31-12-2025", "description": "Q4 2025"},
        {"end_date": None, "description": "Latest quarter"},
    ]
    
    results = []
    
    for test_case in test_cases:
        end_date = test_case["end_date"]
        description = test_case["description"]
        
        print(f"\n📅 Testing: {description}")
        if end_date:
            print(f"   Date: {end_date}")
        
        success = await test_seasonal_trend_sorting(end_date)
        results.append({"quarter": description, "sorted_correctly": success})
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n📊 Summary:")
    print("=" * 60)
    correct_count = sum(1 for result in results if result["sorted_correctly"])
    total_count = len(results)
    
    for result in results:
        status = "✅" if result["sorted_correctly"] else "❌"
        print(f"   {status} {result['quarter']}")
    
    print(f"\n🎯 Overall: {correct_count}/{total_count} quarters sorted correctly")
    
    return correct_count == total_count

async def test_edge_cases():
    """Test edge cases for sorting"""
    
    print("\n🚨 Testing Edge Cases")
    print("=" * 60)
    
    # Test with different date formats that might affect sorting
    edge_cases = [
        {"end_date": "31-01-2025", "description": "Q1 2025 (January)"},
        {"end_date": "28-02-2025", "description": "Q1 2025 (February)"},
        {"end_date": "31-03-2025", "description": "Q1 2025 (March)"},
    ]
    
    for test_case in edge_cases:
        end_date = test_case["end_date"]
        description = test_case["description"]
        
        print(f"\n📅 Testing edge case: {description}")
        success = await test_seasonal_trend_sorting(end_date)
        
        if success:
            print(f"   ✅ {description} - Sorting works correctly")
        else:
            print(f"   ❌ {description} - Sorting issue detected")
        
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    print("Seasonal Trend Sorting Test")
    print("=" * 60)
    
    # Test single quarter
    print("🎯 Testing Single Quarter")
    success1 = asyncio.run(test_seasonal_trend_sorting())
    
    # Test multiple quarters
    print("\n" + "=" * 60)
    success2 = asyncio.run(test_multiple_quarters())
    
    # Test edge cases
    print("\n" + "=" * 60)
    asyncio.run(test_edge_cases())
    
    print(f"\n🎉 Test completed!")
    if success1 and success2:
        print(f"   ✅ All sorting tests passed!")
        print(f"   📈 Commodities are correctly sorted by growth percentage (highest to lowest)")
    else:
        print(f"   ❌ Some sorting tests failed!")
        print(f"   🔧 Please check the implementation") 