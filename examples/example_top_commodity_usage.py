#!/usr/bin/env python3
"""
Example usage of the new top commodity by country API endpoint.
Shows how to call the API and process the results.
"""

import asyncio
import aiohttp
import json

async def get_top_commodity_by_country(end_date: str = None, country_id: str = None):
    """
    Get the top commodity from every country
    
    Args:
        end_date: Optional date in DD-MM-YYYY format (e.g., "31-12-2024")
        country_id: Optional country ID to filter by (e.g., "US", "CN", "ID")
    """
    
    # Build the URL
    url = "http://0.0.0.0:8000/api/v1/export/top-commodity-by-country"
    params = []
    
    if end_date:
        params.append(f"endDate={end_date}")
    if country_id:
        params.append(f"countryId={country_id}")
    
    if params:
        url += "?" + "&".join(params)
    
    print(f"🌍 Fetching top commodity by country...")
    print(f"   End Date: {end_date or 'Latest'}")
    print(f"   Country ID: {country_id or 'All countries'}")
    print(f"   URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"❌ Error: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

async def analyze_top_commodities(data):
    """Analyze the top commodities data"""
    
    if not data or 'data' not in data:
        print("❌ No data received")
        return
    
    countries = data['data']
    print(f"\n📊 Analysis Results:")
    print(f"   Total countries: {len(countries)}")
    
    if not countries:
        print("   ⚠️  No countries found")
        return
    
    # Show top 5 countries by commodity value
    print(f"\n🏆 Top 5 Countries by Commodity Value:")
    print("-" * 60)
    
    for i, country in enumerate(countries[:5]):
        country_name = country.get('countryName', 'Unknown')
        top_commodity = country.get('topCommodity', {})
        
        commodity_name = top_commodity.get('name', 'Unknown')
        commodity_value_usd = top_commodity.get('valueUSD', 0)
        commodity_value_idr = top_commodity.get('valueIDR', 0)
        commodity_growth = top_commodity.get('growth', 0)
        commodity_price = top_commodity.get('price', 'N/A')
        commodity_netweight = top_commodity.get('netweight', 0)
        
        print(f"{i+1}. {country_name}")
        print(f"   Top Commodity: {commodity_name}")
        print(f"   Value: ${commodity_value_usd:,.2f} (Rp {commodity_value_idr:,.0f})")
        print(f"   Growth: {commodity_growth}%")
        print(f"   Price: {commodity_price}")
        print(f"   Net Weight: {commodity_netweight:,.2f} kg")
        print()

async def find_commodity_occurrences(data):
    """Find which commodities appear most frequently as top commodities"""
    
    if not data or 'data' not in data:
        return
    
    countries = data['data']
    
    # Count commodity occurrences
    commodity_counts = {}
    commodity_values = {}
    
    for country in countries:
        top_commodity = country.get('topCommodity', {})
        commodity_name = top_commodity.get('name', 'Unknown')
        commodity_value = top_commodity.get('valueUSD', 0)
        
        if commodity_name not in commodity_counts:
            commodity_counts[commodity_name] = 0
            commodity_values[commodity_name] = 0
        
        commodity_counts[commodity_name] += 1
        commodity_values[commodity_name] += commodity_value
    
    # Sort by count descending
    sorted_commodities = sorted(commodity_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"📈 Most Common Top Commodities:")
    print("-" * 60)
    
    for commodity_name, count in sorted_commodities[:5]:
        total_value = commodity_values[commodity_name]
        print(f"   {commodity_name}: {count} countries (Total: ${total_value:,.2f})")

async def growth_analysis(data):
    """Analyze growth patterns"""
    
    if not data or 'data' not in data:
        return
    
    countries = data['data']
    
    # Separate positive and negative growth
    positive_growth = []
    negative_growth = []
    
    for country in countries:
        top_commodity = country.get('topCommodity', {})
        growth = top_commodity.get('growth', 0)
        country_name = country.get('countryName', 'Unknown')
        commodity_name = top_commodity.get('name', 'Unknown')
        
        if growth > 0:
            positive_growth.append({
                'country': country_name,
                'commodity': commodity_name,
                'growth': growth
            })
        elif growth < 0:
            negative_growth.append({
                'country': country_name,
                'commodity': commodity_name,
                'growth': growth
            })
    
    print(f"📈 Growth Analysis:")
    print("-" * 60)
    print(f"   Countries with positive growth: {len(positive_growth)}")
    print(f"   Countries with negative growth: {len(negative_growth)}")
    
    if positive_growth:
        # Sort by growth descending
        positive_growth.sort(key=lambda x: x['growth'], reverse=True)
        print(f"\n   🟢 Top 3 Positive Growth:")
        for i, item in enumerate(positive_growth[:3]):
            print(f"      {i+1}. {item['country']} - {item['commodity']}: +{item['growth']}%")
    
    if negative_growth:
        # Sort by growth ascending (most negative first)
        negative_growth.sort(key=lambda x: x['growth'])
        print(f"\n   🔴 Top 3 Negative Growth:")
        for i, item in enumerate(negative_growth[:3]):
            print(f"      {i+1}. {item['country']} - {item['commodity']}: {item['growth']}%")

async def main():
    """Main function to demonstrate the API usage"""
    
    print("🚀 Top Commodity by Country API Example")
    print("=" * 60)
    
    # Example 1: Get data for December 2024 (all countries)
    print(f"\n📅 Example 1: December 2024 (All Countries)")
    data_dec = await get_top_commodity_by_country("31-12-2024")
    
    if data_dec:
        await analyze_top_commodities(data_dec)
        await find_commodity_occurrences(data_dec)
        await growth_analysis(data_dec)
    
    # Example 2: Get data for specific country (US)
    print(f"\n📅 Example 2: December 2024 (United States Only)")
    data_us = await get_top_commodity_by_country("31-12-2024", "US")
    
    if data_us:
        await analyze_top_commodities(data_us)
    
    # Example 3: Get data for specific country (China)
    print(f"\n📅 Example 3: December 2024 (China Only)")
    data_cn = await get_top_commodity_by_country("31-12-2024", "CN")
    
    if data_cn:
        await analyze_top_commodities(data_cn)
    
    # Example 4: Get latest data for specific country (Indonesia)
    print(f"\n📅 Example 4: Latest Data (Indonesia Only)")
    data_id = await get_top_commodity_by_country(country_id="ID")
    
    if data_id:
        await analyze_top_commodities(data_id)
    
    # Example 5: Get latest data (all countries)
    print(f"\n📅 Example 5: Latest Available Data (All Countries)")
    data_latest = await get_top_commodity_by_country()
    
    if data_latest:
        await analyze_top_commodities(data_latest)
    
    print(f"\n🎉 Example completed!")
    print(f"   ✅ API endpoint: /top-commodity-by-country")
    print(f"   📊 Returns top commodity from every country")
    print(f"   📅 Supports endDate parameter")
    print(f"   🌍 Supports countryId parameter for filtering")
    print(f"   📈 Includes growth calculations")
    print(f"   💰 Shows values in both USD and IDR")

if __name__ == "__main__":
    asyncio.run(main()) 