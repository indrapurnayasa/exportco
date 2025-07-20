#!/usr/bin/env python3
"""
Test script to verify country demand sorting by growth percentage and commodity growth calculation.
Run this script to test that countries are sorted from highest to lowest growth and commodities have growth data.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any

async def test_country_demand_sorting(end_date: str = None):
    """Test that country demand results are sorted by growth percentage and have commodity growth"""
    
    # Build URL
    base_url = "http://0.0.0.0:8000/api/v1/export/country-demand"
    if end_date:
        url = f"{base_url}?endDate={end_date}"
    else:
        url = base_url
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"🧪 Testing Country Demand Sorting")
            print(f"   URL: {url}")
            print("=" * 60)
            
            # Make the request
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    countries = data.get('data', [])
                    
                    print(f"✅ Request successful! Status: {response.status}")
                    print(f"📊 Total countries returned: {len(countries)}")
                    
                    if len(countries) == 0:
                        print("⚠️  No countries returned")
                        return True, True
                    
                    # Extract country growth percentages
                    country_growth_values = [item.get('growthPercentage', 0) for item in countries]
                    
                    # Check if countries are sorted correctly (highest to lowest)
                    countries_sorted = all(country_growth_values[i] >= country_growth_values[i+1] for i in range(len(country_growth_values)-1))
                    
                    # Check if commodities have growth data and are sorted
                    commodities_with_growth = 0
                    total_commodities = 0
                    products_sorted_correctly = True
                    
                    for country in countries:
                        products = country.get('products', [])
                        total_commodities += len(products)
                        
                        # Check if products are sorted by growth (highest to lowest)
                        if len(products) > 1:
                            product_growths = [p.get('growth', 0) for p in products]
                            is_sorted = all(product_growths[i] >= product_growths[i+1] for i in range(len(product_growths)-1))
                            if not is_sorted:
                                products_sorted_correctly = False
                                print(f"   ⚠️  Products not sorted correctly in {country.get('countryName', 'Unknown')}")
                        
                        for product in products:
                            if product.get('growth') is not None and product.get('growth') != 0.0:
                                commodities_with_growth += 1
                    
                    growth_coverage = (commodities_with_growth / total_commodities * 100) if total_commodities > 0 else 0
                    
                    print(f"\n🔍 Analysis:")
                    print(f"   Countries sorted by growth: {'✅ Yes' if countries_sorted else '❌ No'}")
                    print(f"   Products sorted by growth: {'✅ Yes' if products_sorted_correctly else '❌ No'}")
                    print(f"   Commodities with growth data: {commodities_with_growth}/{total_commodities} ({growth_coverage:.1f}%)")
                    
                    # Show top 10 countries with their growth
                    print(f"\n📈 Top 10 Countries by Growth:")
                    print("-" * 60)
                    for i, country in enumerate(countries[:10]):
                        name = country.get('countryName', 'Unknown')
                        growth = country.get('growthPercentage', 0)
                        transaction = country.get('currentTotalTransaction', 0)
                        products = len(country.get('products', []))
                        
                        print(f"{i+1:2d}. {name[:30]:<30} {growth:>8.2f}%  {transaction:>15,.0f} IDR  {products:>2d} products")
                    
                    # Show sample commodities with growth
                    print(f"\n📦 Sample Commodities with Growth:")
                    print("-" * 60)
                    sample_count = 0
                    for country in countries[:3]:  # First 3 countries
                        if sample_count >= 5:  # Show max 5 samples
                            break
                        for product in country.get('products', [])[:2]:  # First 2 products per country
                            if sample_count >= 5:
                                break
                            country_name = country.get('countryName', 'Unknown')
                            product_name = product.get('name', 'Unknown')
                            growth = product.get('growth', 0)
                            price = product.get('price', 'N/A')
                            
                            print(f"   {country_name[:20]:<20} | {product_name[:25]:<25} | {growth:>8.2f}% | {price}")
                            sample_count += 1
                    
                    # Show growth values for verification
                    print(f"\n📊 Country Growth Values (first 10):")
                    print(f"   {country_growth_values[:10]}")
                    
                    # Check for any anomalies
                    if len(country_growth_values) > 1:
                        max_growth = max(country_growth_values)
                        min_growth = min(country_growth_values)
                        print(f"\n📊 Growth Range:")
                        print(f"   Highest: {max_growth:.2f}%")
                        print(f"   Lowest: {min_growth:.2f}%")
                        print(f"   Range: {max_growth - min_growth:.2f}%")
                    
                    return countries_sorted, growth_coverage > 50, products_sorted_correctly  # Consider success if >50% have growth data and products are sorted
                    
                else:
                    print(f"❌ Request failed! Status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False, False
                    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False, False

async def test_multiple_quarters():
    """Test sorting and growth calculation across multiple quarters"""
    
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
        
        countries_sorted, growth_calculated, products_sorted = await test_country_demand_sorting(end_date)
        results.append({
            "quarter": description, 
            "countries_sorted": countries_sorted, 
            "growth_calculated": growth_calculated,
            "products_sorted": products_sorted
        })
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n📊 Summary:")
    print("=" * 60)
    sorted_count = sum(1 for result in results if result["countries_sorted"])
    growth_count = sum(1 for result in results if result["growth_calculated"])
    products_sorted_count = sum(1 for result in results if result["products_sorted"])
    total_count = len(results)
    
    for result in results:
        sorted_status = "✅" if result["countries_sorted"] else "❌"
        growth_status = "✅" if result["growth_calculated"] else "❌"
        products_status = "✅" if result["products_sorted"] else "❌"
        print(f"   {sorted_status} {growth_status} {products_status} {result['quarter']}")
    
    print(f"\n🎯 Overall:")
    print(f"   Countries sorted: {sorted_count}/{total_count}")
    print(f"   Growth calculated: {growth_count}/{total_count}")
    print(f"   Products sorted: {products_sorted_count}/{total_count}")
    
    return sorted_count == total_count and growth_count == total_count and products_sorted_count == total_count

async def test_commodity_growth_details():
    """Test detailed commodity growth calculation"""
    
    print("\n🔬 Testing Commodity Growth Details")
    print("=" * 60)
    
    url = "http://0.0.0.0:8000/api/v1/export/country-demand"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    countries = data.get('data', [])
                    
                    if len(countries) == 0:
                        print("⚠️  No countries returned")
                        return
                    
                    # Analyze commodity growth patterns
                    all_growth_values = []
                    growth_by_commodity = {}
                    
                    for country in countries:
                        for product in country.get('products', []):
                            growth = product.get('growth', 0)
                            commodity_id = product.get('id', 'Unknown')
                            all_growth_values.append(growth)
                            
                            if commodity_id not in growth_by_commodity:
                                growth_by_commodity[commodity_id] = []
                            growth_by_commodity[commodity_id].append(growth)
                    
                    print(f"📊 Commodity Growth Analysis:")
                    print(f"   Total commodity entries: {len(all_growth_values)}")
                    print(f"   Unique commodities: {len(growth_by_commodity)}")
                    print(f"   Average growth: {sum(all_growth_values) / len(all_growth_values):.2f}%" if all_growth_values else "N/A")
                    
                    # Show top performing commodities
                    print(f"\n🏆 Top Performing Commodities:")
                    commodity_avg_growth = []
                    for commodity_id, growths in growth_by_commodity.items():
                        avg_growth = sum(growths) / len(growths)
                        commodity_avg_growth.append((commodity_id, avg_growth, len(growths)))
                    
                    # Sort by average growth
                    commodity_avg_growth.sort(key=lambda x: x[1], reverse=True)
                    
                    for i, (commodity_id, avg_growth, count) in enumerate(commodity_avg_growth[:5]):
                        print(f"   {i+1}. {commodity_id}: {avg_growth:.2f}% (in {count} countries)")
                    
                else:
                    print(f"❌ Request failed! Status: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    print("Country Demand Sorting and Growth Test")
    print("=" * 60)
    
    # Test single quarter
    print("🎯 Testing Single Quarter")
    countries_sorted, growth_calculated, products_sorted = asyncio.run(test_country_demand_sorting())
    
    # Test multiple quarters
    print("\n" + "=" * 60)
    success2 = asyncio.run(test_multiple_quarters())
    
    # Test commodity growth details
    print("\n" + "=" * 60)
    asyncio.run(test_commodity_growth_details())
    
    print(f"\n🎉 Test completed!")
    if countries_sorted and growth_calculated and products_sorted and success2:
        print(f"   ✅ All tests passed!")
        print(f"   📈 Countries are correctly sorted by growth percentage (highest to lowest)")
        print(f"   📦 Products are correctly sorted by growth percentage (highest to lowest)")
        print(f"   📊 Commodities have growth data calculated")
    else:
        print(f"   ❌ Some tests failed!")
        print(f"   🔧 Please check the implementation") 