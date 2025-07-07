"""
Example queries for ExportData model and service
This file demonstrates various ways to query the export_data table
"""

from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.export_data_service import ExportDataService
from app.schemas.export_data import ExportDataCreate, ExportDataFilter

def example_queries():
    """Demonstrate various query methods"""
    
    # Get database session
    db: Session = SessionLocal()
    export_service = ExportDataService(db)
    
    try:
        print("=== Export Data Query Examples ===\n")
        
        # 1. Get all export data with pagination
        print("1. Getting all export data (first 10 records):")
        all_data = export_service.get_all(skip=0, limit=10)
        print(f"   Found {len(all_data)} records")
        for record in all_data[:3]:  # Show first 3
            print(f"   - ID: {record.id}, Province: {record.provorig}, Value: {record.value}")
        print()
        
        # 2. Get data by specific province
        print("2. Getting data by province (example: 'DKI JAKARTA'):")
        prov_data = export_service.get_by_provorig("DKI JAKARTA", skip=0, limit=5)
        print(f"   Found {len(prov_data)} records for DKI JAKARTA")
        for record in prov_data[:2]:
            print(f"   - ID: {record.id}, Value: {record.value}, Country: {record.ctr}")
        print()
        
        # 3. Get data by country
        print("3. Getting data by country (example: 'SINGAPURA'):")
        country_data = export_service.get_by_ctr("SINGAPURA", skip=0, limit=5)
        print(f"   Found {len(country_data)} records for SINGAPURA")
        for record in country_data[:2]:
            print(f"   - ID: {record.id}, Value: {record.value}, Province: {record.provorig}")
        print()
        
        # 4. Get data by year
        print("4. Getting data by year (example: '2023'):")
        year_data = export_service.get_by_tahun("2023", skip=0, limit=5)
        print(f"   Found {len(year_data)} records for year 2023")
        for record in year_data[:2]:
            print(f"   - ID: {record.id}, Month: {record.bulan}, Value: {record.value}")
        print()
        
        # 5. Get data by month
        print("5. Getting data by month (example: 'Januari'):")
        month_data = export_service.get_by_bulan("Januari", skip=0, limit=5)
        print(f"   Found {len(month_data)} records for January")
        for record in month_data[:2]:
            print(f"   - ID: {record.id}, Year: {record.tahun}, Value: {record.value}")
        print()
        
        # 6. Filter by value range
        print("6. Getting data within value range (1,000,000 to 10,000,000):")
        value_range_data = export_service.get_value_range(
            Decimal("1000000"), 
            Decimal("10000000"), 
            skip=0, 
            limit=5
        )
        print(f"   Found {len(value_range_data)} records in value range")
        for record in value_range_data[:2]:
            print(f"   - ID: {record.id}, Value: {record.value}, Province: {record.provorig}")
        print()
        
        # 7. Search by HS code
        print("7. Searching by HS code (example: '85'):")
        hs_search_data = export_service.search_by_kodehs("85", skip=0, limit=5)
        print(f"   Found {len(hs_search_data)} records with HS code containing '85'")
        for record in hs_search_data[:2]:
            print(f"   - ID: {record.id}, HS Code: {record.kodehs}, Value: {record.value}")
        print()
        
        # 8. Complex filtering
        print("8. Complex filtering (multiple criteria):")
        filters = ExportDataFilter(
            provorig="DKI JAKARTA",
            tahun="2023",
            min_value=Decimal("1000000"),
            max_value=Decimal("50000000")
        )
        filtered_data = export_service.filter_data(filters, skip=0, limit=5)
        print(f"   Found {len(filtered_data)} records matching complex criteria")
        for record in filtered_data[:2]:
            print(f"   - ID: {record.id}, Value: {record.value}, Country: {record.ctr}")
        print()
        
        # 9. Get statistics
        print("9. Getting overall statistics:")
        stats = export_service.get_statistics()
        print(f"   Total records: {stats['total_records']}")
        print(f"   Total value: {stats['total_value']:,.2f}")
        print(f"   Total netweight: {stats['total_netweight']:,.2f}")
        print(f"   Unique provinces: {stats['unique_provinces']}")
        print(f"   Unique countries: {stats['unique_countries']}")
        print(f"   Unique ports: {stats['unique_ports']}")
        print(f"   Unique years: {stats['unique_years']}")
        print()
        
        # 10. Get data by date range
        print("10. Getting data by date range (last 30 days):")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range_data = export_service.get_by_date_range(start_date, end_date, skip=0, limit=5)
        print(f"   Found {len(date_range_data)} records in the last 30 days")
        for record in date_range_data[:2]:
            print(f"   - ID: {record.id}, Created: {record.created_at}, Value: {record.value}")
        print()
        
    except Exception as e:
        print(f"Error during queries: {e}")
    finally:
        db.close()

def create_sample_data():
    """Create sample export data for testing"""
    
    db: Session = SessionLocal()
    export_service = ExportDataService(db)
    
    try:
        # Sample data
        sample_records = [
            ExportDataCreate(
                provorig="DKI JAKARTA",
                value=Decimal("5000000"),
                netweight=Decimal("1000.5"),
                kodehs="85171200",
                pod="SINGAPURA",
                ctr="SINGAPURA",
                tahun="2023",
                bulan="Januari",
                ctr_code="SG",
                comodity_code="8517"
            ),
            ExportDataCreate(
                provorig="JAWA BARAT",
                value=Decimal("7500000"),
                netweight=Decimal("1500.75"),
                kodehs="85287200",
                pod="MALAYSIA",
                ctr="MALAYSIA",
                tahun="2023",
                bulan="Februari",
                ctr_code="MY",
                comodity_code="8528"
            ),
            ExportDataCreate(
                provorig="DKI JAKARTA",
                value=Decimal("3000000"),
                netweight=Decimal("800.25"),
                kodehs="85444900",
                pod="THAILAND",
                ctr="THAILAND",
                tahun="2023",
                bulan="Januari",
                ctr_code="TH",
                comodity_code="8544"
            )
        ]
        
        print("Creating sample export data...")
        for record in sample_records:
            created = export_service.create(record)
            print(f"Created record with ID: {created.id}")
        
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Uncomment the line below to create sample data first
    # create_sample_data()
    
    # Run example queries
    example_queries() 