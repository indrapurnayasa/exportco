"""
Script untuk menambahkan data kurs mata uang ke database
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models.currency_rates import CurrencyRates
from sqlalchemy import select
from datetime import date, datetime

async def add_currency_rates():
    """Add sample currency rates to currency_rates table"""
    
    # Sample currency rate data
    currency_rates_data = [
        {
            "base_currency": "IDR",
            "target_currency": "USD",
            "rate": 0.000064,  # 1 IDR = 0.000064 USD (approximately 1 USD = 15,625 IDR)
            "rate_date": date(2024, 1, 15)
        },
        {
            "base_currency": "IDR", 
            "target_currency": "USD",
            "rate": 0.000065,  # 1 IDR = 0.000065 USD (approximately 1 USD = 15,385 IDR)
            "rate_date": date(2024, 2, 15)
        },
        {
            "base_currency": "IDR",
            "target_currency": "USD", 
            "rate": 0.000066,  # 1 IDR = 0.000066 USD (approximately 1 USD = 15,152 IDR)
            "rate_date": date(2024, 3, 15)
        },
        {
            "base_currency": "USD",
            "target_currency": "IDR",
            "rate": 15625.0,  # 1 USD = 15,625 IDR
            "rate_date": date(2024, 1, 15)
        },
        {
            "base_currency": "USD",
            "target_currency": "IDR",
            "rate": 15385.0,  # 1 USD = 15,385 IDR
            "rate_date": date(2024, 2, 15)
        },
        {
            "base_currency": "USD",
            "target_currency": "IDR",
            "rate": 15152.0,  # 1 USD = 15,152 IDR
            "rate_date": date(2024, 3, 15)
        }
    ]
    
    try:
        # Get database session
        async for db in get_async_db():
            try:
                # Check if currency rates already exist
                result = await db.execute(select(CurrencyRates))
                existing_rates = result.scalars().all()
                
                if existing_rates:
                    print(f"✅ Currency rates already exist ({len(existing_rates)} records)")
                    print("   Sample records:")
                    for rate in existing_rates[:3]:
                        print(f"   - {rate.base_currency} to {rate.target_currency}: {rate.rate} (date: {rate.rate_date})")
                    return
                
                # Add new currency rates
                for rate_data in currency_rates_data:
                    new_rate = CurrencyRates(
                        base_currency=rate_data["base_currency"],
                        target_currency=rate_data["target_currency"],
                        rate=rate_data["rate"],
                        rate_date=rate_data["rate_date"],
                        created_at=datetime.now()
                    )
                    db.add(new_rate)
                
                await db.commit()
                
                print(f"✅ Berhasil menambahkan {len(currency_rates_data)} currency rates")
                print("   Sample rates added:")
                for rate_data in currency_rates_data[:3]:
                    print(f"   - {rate_data['base_currency']} to {rate_data['target_currency']}: {rate_data['rate']} (date: {rate_data['rate_date']})")
                
            except Exception as e:
                print(f"❌ Error adding currency rates: {e}")
                await db.rollback()
            finally:
                await db.close()
                break
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    print("🔄 Adding currency rates to database...")
    asyncio.run(add_currency_rates())
    print("✅ Done!") 