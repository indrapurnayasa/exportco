#!/usr/bin/env python3
"""
Script to add sample USD to IDR exchange rates for testing.
Run this script to add currency rate data if needed for testing.
"""

import asyncio
from datetime import date, datetime
from sqlalchemy import text
from app.db.database import get_async_db
from app.models.currency_rates import CurrencyRates

async def add_sample_currency_rates():
    """Add sample USD to IDR exchange rates"""
        async for db in get_async_db():
            try:
            print("Adding sample USD to IDR exchange rates...")
            
            # Check if rates already exist
            result = await db.execute(
                text("SELECT COUNT(*) FROM currency_rates WHERE base_currency = 'USD' AND target_currency = 'IDR'")
            )
            existing_count = result.scalar()
                
            if existing_count > 0:
                print(f"✅ {existing_count} USD to IDR exchange rates already exist")
                    return
                
            # Add sample rates for the last 30 days
            sample_rates = [
                {"rate": 15500.00, "date": date.today()},
                {"rate": 15450.00, "date": date.today()},
                {"rate": 15600.00, "date": date.today()},
                {"rate": 15400.00, "date": date.today()},
                {"rate": 15550.00, "date": date.today()},
            ]
            
            for rate_data in sample_rates:
                currency_rate = CurrencyRates(
                    base_currency='USD',
                    target_currency='IDR',
                    rate=rate_data['rate'],
                    rate_date=rate_data['date'],
                        created_at=datetime.now()
                    )
                db.add(currency_rate)
                
                await db.commit()
            print("✅ Sample USD to IDR exchange rates added successfully!")
            print(f"   Added {len(sample_rates)} exchange rates")
            print("   Latest rate: 1 USD = 15,500 IDR")
                
            except Exception as e:
                print(f"❌ Error adding currency rates: {e}")
                await db.rollback()
            finally:
                break

async def check_currency_rates():
    """Check existing currency rates"""
    async for db in get_async_db():
        try:
            result = await db.execute(
                text("""
                    SELECT base_currency, target_currency, rate, rate_date, created_at
                    FROM currency_rates 
                    WHERE base_currency = 'USD' AND target_currency = 'IDR'
                    ORDER BY rate_date DESC, created_at DESC
                    LIMIT 5
                """)
            )
            
            rates = result.fetchall()
            print(f"\n📊 Current USD to IDR Exchange Rates ({len(rates)} found):")
            for rate in rates:
                print(f"   {rate.rate_date}: 1 {rate.base_currency} = {rate.rate:,.2f} {rate.target_currency}")
                
    except Exception as e:
            print(f"❌ Error checking currency rates: {e}")
        finally:
            break

if __name__ == "__main__":
    print("Currency Rates Management")
    print("=" * 40)
    
    # Check existing rates first
    asyncio.run(check_currency_rates())
    
    # Ask user if they want to add sample rates
    response = input("\nDo you want to add sample USD to IDR exchange rates? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        asyncio.run(add_sample_currency_rates())
    else:
        print("Skipping currency rate creation.")
    
    print("\nNote: The country demand endpoint will use the latest USD to IDR exchange rate for currency conversion.") 