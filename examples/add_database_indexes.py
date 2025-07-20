#!/usr/bin/env python3
"""
Script to add database indexes for improved query performance.
Run this script to add indexes that will significantly speed up the country demand queries.
"""

import asyncio
from sqlalchemy import text
from app.db.database import get_async_db
from app.core.config import settings

async def add_performance_indexes():
    """Add database indexes to improve query performance"""
    async for db in get_async_db():
        try:
            print("Adding database indexes for improved performance...")
            
            # Index for country demand queries
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_country_demand 
                ON export_data (tahun, ctr_code, bulan, value, netweight, comodity_code)
                WHERE ctr_code IS NOT NULL AND value IS NOT NULL
            """))
            
            # Index for year and month filtering
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_year_month 
                ON export_data (tahun, bulan)
            """))
            
            # Index for country code lookups
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_ctr_code 
                ON export_data (ctr_code)
                WHERE ctr_code IS NOT NULL
            """))
            
            # Index for commodity code lookups
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_commodity 
                ON export_data (comodity_code)
                WHERE comodity_code IS NOT NULL
            """))
            
            # Index for value aggregations
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_value 
                ON export_data (value)
                WHERE value IS NOT NULL
            """))
            
            # Index for netweight aggregations
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_netweight 
                ON export_data (netweight)
                WHERE netweight IS NOT NULL
            """))
            
            # Index for seasonal trend queries (comodity_code + netweight)
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_seasonal_trend 
                ON export_data (tahun, comodity_code, bulan, netweight)
                WHERE comodity_code IS NOT NULL AND netweight IS NOT NULL
            """))
            
            # Index for year and month sorting (for latest quarter detection)
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_year_month_sort 
                ON export_data (tahun DESC, bulan DESC)
                WHERE tahun IS NOT NULL AND bulan IS NOT NULL
            """))
            
            # Index for commodity-country aggregations
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_export_data_commodity_country 
                ON export_data (comodity_code, ctr_code, netweight)
                WHERE comodity_code IS NOT NULL AND ctr_code IS NOT NULL AND netweight IS NOT NULL
            """))
            
            await db.commit()
            print("✅ Database indexes added successfully!")
            print("\nIndexes created:")
            print("- idx_export_data_country_demand: Composite index for country demand queries")
            print("- idx_export_data_year_month: Index for year/month filtering")
            print("- idx_export_data_ctr_code: Index for country code lookups")
            print("- idx_export_data_commodity: Index for commodity code lookups")
            print("- idx_export_data_value: Index for value aggregations")
            print("- idx_export_data_netweight: Index for netweight aggregations")
            print("- idx_export_data_seasonal_trend: Index for seasonal trend queries")
            print("- idx_export_data_year_month_sort: Index for latest quarter detection")
            print("- idx_export_data_commodity_country: Index for commodity-country aggregations")
            
        except Exception as e:
            print(f"❌ Error adding indexes: {e}")
            await db.rollback()
        finally:
            break

async def check_existing_indexes():
    """Check existing indexes on the export_data table"""
    async for db in get_async_db():
        try:
            result = await db.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'export_data'
                ORDER BY indexname
            """))
            
            indexes = result.fetchall()
            print(f"\nExisting indexes on export_data table ({len(indexes)} found):")
            for idx in indexes:
                print(f"- {idx.indexname}")
                
        except Exception as e:
            print(f"❌ Error checking indexes: {e}")
        finally:
            break

if __name__ == "__main__":
    print("Database Index Management Script")
    print("=" * 40)
    
    # Check existing indexes first
    asyncio.run(check_existing_indexes())
    
    # Ask user if they want to add indexes
    response = input("\nDo you want to add performance indexes? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        asyncio.run(add_performance_indexes())
    else:
        print("Skipping index creation.")
    
    print("\nNote: After adding indexes, the first few queries might be slower as the database builds the indexes.")
    print("Subsequent queries should be significantly faster.") 