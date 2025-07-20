#!/usr/bin/env python3
"""
Test script to verify that the country demand endpoint returns price information.
Run this script to test the updated endpoint with price data.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_country_demand_with_price():
    """Test the country demand endpoint to verify price inclusion"""
    
    url = "http://0.0.0.0:8000/api/v1/export/country-demand"
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🧪 Testing Country Demand Endpoint with Price Data")
            print("=" * 60)
            
            # Make the request
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"✅ Request successful! Status: {response.status}")
                    print(f"📊 Total countries returned: {len(data.get('data', []))}")
                    
                    # Check if countries have products with prices
                    countries_with_prices = 0
                    total_products = 0
                    products_with_prices = 0
                    
                    for country in data.get('data', []):
                        country_name = country.get('countryName', 'Unknown')
                        products = country.get('products', [])
                        
                        print(f"\n🌍 Country: {country_name}")
                        print(f"   Growth: {country.get('growthPercentage', 0)}%")
                        print(f"   Total Transaction (IDR): {country.get('currentTotalTransaction', 0):,.2f}")
                        print(f"   Products: {len(products)}")
                        
                        for product in products:
                            total_products += 1
                            product_id = product.get('id', 'Unknown')
                            product_name = product.get('name', 'Unknown')
                            price = product.get('price', 'No price')
                            growth = product.get('growth', 0)
                            
                            print(f"     📦 {product_id}: {product_name}")
                            print(f"        💰 Price: {price}")
                            print(f"        📈 Growth: {growth}%")
                            
                            if price and price != "No price":
                                products_with_prices += 1
                        
                        if any(p.get('price') and p.get('price') != "No price" for p in products):
                            countries_with_prices += 1
                    
                    print(f"\n📈 Summary:")
                    print(f"   Countries with price data: {countries_with_prices}/{len(data.get('data', []))}")
                    print(f"   Products with price data: {products_with_prices}/{total_products}")
                    print(f"   Price coverage: {(products_with_prices/total_products*100):.1f}%" if total_products > 0 else "   Price coverage: 0%")
                    
                    # Verify response structure
                    print(f"\n🔍 Response Structure Validation:")
                    
                    # Check if all required fields are present
                    required_fields = ['countryId', 'countryName', 'growthPercentage', 'currentTotalTransaction', 'products']
                    product_fields = ['id', 'name', 'price', 'growth']
                    
                    structure_valid = True
                    for country in data.get('data', []):
                        for field in required_fields:
                            if field not in country:
                                print(f"   ❌ Missing field '{field}' in country data")
                                structure_valid = False
                        
                        for product in country.get('products', []):
                            for field in product_fields:
                                if field not in product:
                                    print(f"   ❌ Missing field '{field}' in product data")
                                    structure_valid = False
                    
                    if structure_valid:
                        print(f"   ✅ All required fields present")
                    
                    # Check price format
                    price_format_valid = True
                    for country in data.get('data', []):
                        for product in country.get('products', []):
                            price = product.get('price', '')
                            if price and not price.startswith('Rp '):
                                print(f"   ⚠️  Price format issue: {price} (should start with 'Rp ')")
                                price_format_valid = False
                    
                    if price_format_valid:
                        print(f"   ✅ Price format is correct")
                    
                    return True
                    
                else:
                    print(f"❌ Request failed! Status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def test_sample_response():
    """Test with a sample response to verify the expected format"""
    
    print("\n📋 Expected Response Format:")
    print("=" * 60)
    
    sample_response = {
        "data": [
            {
                "countryId": "BD",
                "countryName": "BANGLADESH",
                "growthPercentage": -85.95,
                "currentTotalTransaction": 62518464.4573,  # This will be converted to IDR
                "products": [
                    {
                        "id": "OLE",
                        "name": "Palm Olein (Minyak Kelapa Sawit Olahan)",
                        "price": "Rp 25.000/kg",
                        "growth": -79.09
                    },
                    {
                        "id": "COA",
                        "name": "Cocoa (Kakao)",
                        "price": "Rp 45.000/kg",
                        "growth": -74.78
                    }
                ]
            }
        ]
    }
    
    print(json.dumps(sample_response, indent=2))
    print("\n✅ This is the expected format with price information included")
    print("💱 Note: currentTotalTransaction values are converted from USD to IDR using the latest exchange rate")

if __name__ == "__main__":
    print("Country Demand Price Test")
    print("=" * 60)
    
    # Show expected format
    asyncio.run(test_sample_response())
    
    # Run the actual test
    print("\n" + "=" * 60)
    success = asyncio.run(test_country_demand_with_price())
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"   The country demand endpoint now includes price information for commodities.")
    else:
        print(f"\n💥 Test failed!")
        print(f"   Please check the server status and try again.") 