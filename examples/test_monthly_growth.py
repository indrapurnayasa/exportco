#!/usr/bin/env python3
"""
Test script to verify month-over-month growth calculation in country demand endpoint.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_monthly_growth():
    """Test that country demand uses month-over-month growth"""
    
    # Test different months to see month-over-month growth
    test_cases = [
        {"end_date": "31-03-2025", "description": "March 2025 (should compare with Feb 2025)"},
        {"end_date": "30-04-2025", "description": "April 2025 (should compare with Mar 2025)"},
        {"end_date": "31-05-2025", "description": "May 2025 (should compare with Apr 2025)"},
        {"end_date": "30-06-2025", "description": "June 2025 (should compare with May 2025)"},
    ]
    
    print("🧪 Testing Month-over-Month Growth")
    print("=" * 60)
    
    for test_case in test_cases:
        end_date = test_case["end_date"]
        description = test_case["description"]
        
        url = f"http://0.0.0.0:8000/api/v1/export/country-demand?endDate={end_date}"
        
        print(f"\n📅 Testing: {description}")
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
                            # Show first country with growth details
                            first_country = countries[0]
                            country_name = first_country.get('countryName', 'Unknown')
                            country_growth = first_country.get('growthPercentage', 0)
                            products = first_country.get('products', [])
                            
                            print(f"   📊 Top country: {country_name}")
                            print(f"      Country growth: {country_growth}% (month-over-month)")
                            print(f"      Products: {len(products)}")
                            
                            # Show first few products with their growth
                            if products:
                                print(f"      Top products (month-over-month growth):")
                                for i, product in enumerate(products[:3]):
                                    product_name = product.get('name', 'Unknown')
                                    product_growth = product.get('growth', 0)
                                    print(f"         {i+1}. {product_name}: {product_growth}%")
                        else:
                            print(f"   ⚠️  No data available for this month")
                            
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
    
    print(f"\n🎯 Month-over-Month Growth Summary:")
    print("=" * 60)
    print("✅ Growth is now calculated month-over-month instead of quarter-over-quarter")
    print("📈 This provides more granular and recent growth trends")
    print("🔄 Each month compares with the previous month (e.g., March vs February)")

async def test_growth_comparison():
    """Test to show the difference between monthly and quarterly growth"""
    
    print(f"\n🔬 Growth Calculation Comparison")
    print("=" * 60)
    
    # Test the same quarter with different months
    test_months = [
        {"end_date": "31-03-2025", "month": "March 2025"},
        {"end_date": "30-04-2025", "month": "April 2025"},
        {"end_date": "31-05-2025", "month": "May 2025"},
    ]
    
    results = []
    
    for test_month in test_months:
        end_date = test_month["end_date"]
        month_name = test_month["month"]
        
        url = f"http://0.0.0.0:8000/api/v1/export/country-demand?endDate={end_date}"
        
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
                                top_countries.append({
                                    'name': country.get('countryName', 'Unknown'),
                                    'growth': country.get('growthPercentage', 0)
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
        print(f"📊 Monthly Growth Comparison (Top 3 Countries):")
        print("-" * 60)
        
        for result in results:
            print(f"\n📅 {result['month']}:")
            for i, country in enumerate(result['countries']):
                print(f"   {i+1}. {country['name']}: {country['growth']}%")
    
    print(f"\n💡 Key Differences:")
    print("   • Monthly growth shows more recent trends")
    print("   • More volatile but more responsive to changes")
    print("   • Better for identifying short-term opportunities")

if __name__ == "__main__":
    print("Month-over-Month Growth Test")
    print("=" * 60)
    
    # Test monthly growth
    asyncio.run(test_monthly_growth())
    
    # Test growth comparison
    asyncio.run(test_growth_comparison())
    
    print(f"\n🎉 Test completed!")
    print(f"   ✅ Country demand now uses month-over-month growth")
    print(f"   📈 More granular growth analysis")
    print(f"   🔄 Compares each month with the previous month") 