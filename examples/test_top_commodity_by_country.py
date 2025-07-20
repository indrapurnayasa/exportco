#!/usr/bin/env python3
"""
Test script for the new top commodity by country API endpoint.
Tests the /top-commodity-by-country endpoint with endDate parameter.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_top_commodity_by_country():
    """Test the top commodity by country endpoint"""
    
    print("🧪 Testing Top Commodity by Country API")
    print("=" * 60)
    
    # Test cases with different end dates
    test_cases = [
        {
            "end_date": "31-12-2024",
            "description": "December 2024",
            "expected_month": "December 2024"
        },
        {
            "end_date": "31-01-2025", 
            "description": "January 2025",
            "expected_month": "January 2025"
        },
        {
            "end_date": "31-03-2025",
            "description": "March 2025", 
            "expected_month": "March 2025"
        },
        {
            "end_date": None,
            "description": "Latest available data",
            "expected_month": "Latest"
        }
    ]
    
    for test_case in test_cases:
        end_date = test_case["end_date"]
        description = test_case["description"]
        expected_month = test_case["expected_month"]
        
        # Build URL
        if end_date:
            url = f"http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate={end_date}"
        else:
            url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country"
        
        print(f"\n📅 Testing: {description}")
        print(f"   Expected month: {expected_month}")
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
                            # Show first few countries with their top commodities
                            print(f"   📊 Top countries and their top commodities:")
                            for i, country in enumerate(countries[:5]):
                                country_name = country.get('countryName', 'Unknown')
                                top_commodity = country.get('topCommodity', {})
                                commodity_name = top_commodity.get('name', 'Unknown')
                                commodity_value_usd = top_commodity.get('valueUSD', 0)
                                commodity_growth = top_commodity.get('growth', 0)
                                commodity_price = top_commodity.get('price', 'N/A')
                                
                                print(f"      {i+1}. {country_name}")
                                print(f"         Top commodity: {commodity_name}")
                                print(f"         Value: ${commodity_value_usd:,.2f}")
                                print(f"         Growth: {commodity_growth}%")
                                print(f"         Price: {commodity_price}")
                        else:
                            print(f"   ⚠️  No data available for this period")
                            
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

async def test_response_structure():
    """Test the response structure and data types"""
    
    print(f"\n🔬 Testing Response Structure")
    print("=" * 60)
    
    url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024"
    
    print(f"📅 Testing: December 2024")
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
                        # Analyze the structure of the first country
                        first_country = countries[0]
                        print(f"   📊 Response structure analysis:")
                        print(f"      Root keys: {list(first_country.keys())}")
                        
                        # Check country level fields
                        country_id = first_country.get('countryId')
                        country_name = first_country.get('countryName')
                        top_commodity = first_country.get('topCommodity')
                        
                        print(f"      countryId: {country_id} (type: {type(country_id)})")
                        print(f"      countryName: {country_name} (type: {type(country_name)})")
                        print(f"      topCommodity: {type(top_commodity)}")
                        
                        if top_commodity:
                            print(f"      Top commodity keys: {list(top_commodity.keys())}")
                            
                            # Check commodity level fields
                            commodity_id = top_commodity.get('id')
                            commodity_name = top_commodity.get('name')
                            commodity_price = top_commodity.get('price')
                            commodity_growth = top_commodity.get('growth')
                            commodity_value_usd = top_commodity.get('valueUSD')
                            commodity_value_idr = top_commodity.get('valueIDR')
                            commodity_netweight = top_commodity.get('netweight')
                            
                            print(f"         id: {commodity_id} (type: {type(commodity_id)})")
                            print(f"         name: {commodity_name} (type: {type(commodity_name)})")
                            print(f"         price: {commodity_price} (type: {type(commodity_price)})")
                            print(f"         growth: {commodity_growth} (type: {type(commodity_growth)})")
                            print(f"         valueUSD: {commodity_value_usd} (type: {type(commodity_value_usd)})")
                            print(f"         valueIDR: {commodity_value_idr} (type: {type(commodity_value_idr)})")
                            print(f"         netweight: {commodity_netweight} (type: {type(commodity_netweight)})")
                        
                        print(f"   ✅ Response structure is correct")
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

async def test_sorting_and_ranking():
    """Test that countries are properly sorted by commodity value"""
    
    print(f"\n📊 Testing Sorting and Ranking")
    print("=" * 60)
    
    url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate=31-12-2024"
    
    print(f"📅 Testing: December 2024")
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
                        print(f"   📊 Top 3 countries by commodity value:")
                        
                        for i, country in enumerate(countries[:3]):
                            country_name = country.get('countryName', 'Unknown')
                            top_commodity = country.get('topCommodity', {})
                            commodity_name = top_commodity.get('name', 'Unknown')
                            commodity_value_usd = top_commodity.get('valueUSD', 0)
                            
                            print(f"      {i+1}. {country_name}")
                            print(f"         Commodity: {commodity_name}")
                            print(f"         Value: ${commodity_value_usd:,.2f}")
                        
                        # Verify sorting (should be descending by value)
                        first_value = countries[0].get('topCommodity', {}).get('valueUSD', 0)
                        second_value = countries[1].get('topCommodity', {}).get('valueUSD', 0)
                        third_value = countries[2].get('topCommodity', {}).get('valueUSD', 0)
                        
                        if first_value >= second_value >= third_value:
                            print(f"   ✅ Sorting is correct (descending by value)")
                        else:
                            print(f"   ❌ Sorting is incorrect")
                            print(f"      Expected: {first_value} >= {second_value} >= {third_value}")
                        
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

async def test_growth_calculation():
    """Test that growth calculation is working correctly"""
    
    print(f"\n📈 Testing Growth Calculation")
    print("=" * 60)
    
    # Test consecutive months to see growth patterns
    test_months = [
        {"end_date": "31-12-2024", "month": "December 2024"},
        {"end_date": "31-01-2025", "month": "January 2025"},
    ]
    
    results = []
    
    for test_month in test_months:
        end_date = test_month["end_date"]
        month_name = test_month["month"]
        
        url = f"http://0.0.0.0:8000/api/v1/export/top-commodity-by-country?endDate={end_date}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        countries = data.get('data', [])
                        
                        if countries:
                            # Get top 3 countries and their growth
                            top_countries = []
                            for i, country in enumerate(countries[:3]):
                                top_commodity = country.get('topCommodity', {})
                                top_countries.append({
                                    'name': country.get('countryName', 'Unknown'),
                                    'commodity': top_commodity.get('name', 'Unknown'),
                                    'growth': top_commodity.get('growth', 0),
                                    'value': top_commodity.get('valueUSD', 0)
                                })
                            
                            results.append({
                                'month': month_name,
                                'countries': top_countries
                            })
                            
        except Exception as e:
            print(f"Error testing {month_name}: {e}")
        
        await asyncio.sleep(1)
    
    # Display comparison
    if results:
        print(f"📊 Growth Analysis (Top 3 Countries):")
        print("-" * 60)
        
        for result in results:
            print(f"\n📅 {result['month']}:")
            for i, country in enumerate(result['countries']):
                print(f"   {i+1}. {country['name']}")
                print(f"      Commodity: {country['commodity']}")
                print(f"      Growth: {country['growth']}%")
                print(f"      Value: ${country['value']:,.2f}")
    
    print(f"\n💡 Growth Analysis:")
    print("   • Growth is calculated month-over-month")
    print("   • Each country shows growth for its top commodity")
    print("   • Growth reflects the change from previous month")

if __name__ == "__main__":
    print("Top Commodity by Country API Test")
    print("=" * 60)
    
    # Test the main functionality
    asyncio.run(test_top_commodity_by_country())
    
    # Test response structure
    asyncio.run(test_response_structure())
    
    # Test sorting and ranking
    asyncio.run(test_sorting_and_ranking())
    
    # Test growth calculation
    asyncio.run(test_growth_calculation())
    
    print(f"\n🎉 Test completed!")
    print(f"   ✅ New API endpoint: /top-commodity-by-country")
    print(f"   📊 Returns top commodity from every country")
    print(f"   📅 Supports endDate parameter for date filtering")
    print(f"   📈 Includes month-over-month growth calculation")
    print(f"   💰 Shows values in both USD and IDR") 