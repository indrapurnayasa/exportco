#!/usr/bin/env python3
"""
Simple test to verify product sorting by growth percentage within countries.
"""

import asyncio
import aiohttp

async def test_product_sorting():
    """Test that products are sorted by growth percentage within each country"""
    
    url = "http://0.0.0.0:8000/api/v1/export/country-demand"
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🧪 Testing Product Sorting by Growth")
            print("=" * 50)
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    countries = data.get('data', [])
                    
                    print(f"✅ Found {len(countries)} countries")
                    
                    if not countries:
                        print("⚠️  No countries returned")
                        return
                    
                    # Check sorting for each country
                    all_sorted = True
                    
                    for i, country in enumerate(countries[:5]):  # Check first 5 countries
                        country_name = country.get('countryName', 'Unknown')
                        products = country.get('products', [])
                        
                        if len(products) < 2:
                            print(f"   {i+1}. {country_name}: Only {len(products)} product(s) - skipping sort check")
                            continue
                        
                        # Extract growth values
                        growth_values = [p.get('growth', 0) for p in products]
                        
                        # Check if sorted (highest to lowest)
                        is_sorted = all(growth_values[j] >= growth_values[j+1] for j in range(len(growth_values)-1))
                        
                        status = "✅" if is_sorted else "❌"
                        print(f"   {i+1}. {country_name}: {status} {len(products)} products")
                        
                        if is_sorted:
                            # Show first few products
                            for j, product in enumerate(products[:3]):
                                print(f"      {j+1}. {product.get('name', 'Unknown')}: {product.get('growth', 0)}%")
                        else:
                            print(f"      ❌ Not sorted! Growth values: {growth_values[:5]}")
                            all_sorted = False
                    
                    print(f"\n🎯 Result: {'✅ All products sorted correctly' if all_sorted else '❌ Some products not sorted'}")
                    
                else:
                    print(f"❌ Request failed: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_product_sorting()) 