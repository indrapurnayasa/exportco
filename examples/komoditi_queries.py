"""
Example queries for Komoditi model and service
This file demonstrates various ways to query the komoditi table
"""

from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.komoditi_service import KomoditiService
from app.schemas.komoditi import KomoditiCreate, KomoditiFilter

def example_queries():
    """Demonstrate various query methods"""
    
    # Get database session
    db: Session = SessionLocal()
    komoditi_service = KomoditiService(db)
    
    try:
        print("=== Komoditi Query Examples ===\n")
        
        # 1. Get all commodities with pagination
        print("1. Getting all commodities (first 10 records):")
        all_data = komoditi_service.get_all(skip=0, limit=10)
        print(f"   Found {len(all_data)} records")
        for record in all_data[:3]:  # Show first 3
            print(f"   - ID: {record.id}, Code: {record.kode_komoditi}, Name: {record.nama_komoditi}, Price: {record.harga_komoditi}")
        print()
        
        # 2. Get commodity by code
        print("2. Getting commodity by code (example: 'K001'):")
        komoditi_by_code = komoditi_service.get_by_kode("K001")
        if komoditi_by_code:
            print(f"   Found: {komoditi_by_code.nama_komoditi} - {komoditi_by_code.harga_komoditi}")
        else:
            print("   No commodity found with code K001")
        print()
        
        # 3. Search by name
        print("3. Searching commodities by name (example: 'Beras'):")
        nama_data = komoditi_service.get_by_nama("Beras", skip=0, limit=5)
        print(f"   Found {len(nama_data)} records containing 'Beras'")
        for record in nama_data[:2]:
            print(f"   - ID: {record.id}, Name: {record.nama_komoditi}, Price: {record.harga_komoditi}")
        print()
        
        # 4. Get by unit
        print("4. Getting commodities by unit (example: 'KG'):")
        unit_data = komoditi_service.get_by_satuan("KG", skip=0, limit=5)
        print(f"   Found {len(unit_data)} records with unit 'KG'")
        for record in unit_data[:2]:
            print(f"   - ID: {record.id}, Name: {record.nama_komoditi}, Price: {record.harga_komoditi}")
        print()
        
        # 5. Filter by price range
        print("5. Getting commodities within price range (10,000 to 100,000):")
        price_range_data = komoditi_service.get_harga_range(
            Decimal("10000"), 
            Decimal("100000"), 
            skip=0, 
            limit=5
        )
        print(f"   Found {len(price_range_data)} records in price range")
        for record in price_range_data[:2]:
            print(f"   - ID: {record.id}, Name: {record.nama_komoditi}, Price: {record.harga_komoditi}")
        print()
        
        # 6. Search by name or code
        print("6. Searching by name or code (example: 'K'):")
        search_data = komoditi_service.search_komoditi("K", skip=0, limit=5)
        print(f"   Found {len(search_data)} records matching 'K'")
        for record in search_data[:2]:
            print(f"   - ID: {record.id}, Code: {record.kode_komoditi}, Name: {record.nama_komoditi}")
        print()
        
        # 7. Complex filtering
        print("7. Complex filtering (multiple criteria):")
        filters = KomoditiFilter(
            satuan_komoditi="KG",
            min_harga=Decimal("5000"),
            max_harga=Decimal("50000")
        )
        filtered_data = komoditi_service.filter_data(filters, skip=0, limit=5)
        print(f"   Found {len(filtered_data)} records matching complex criteria")
        for record in filtered_data[:2]:
            print(f"   - ID: {record.id}, Name: {record.nama_komoditi}, Price: {record.harga_komoditi}")
        print()
        
        # 8. Get statistics
        print("8. Getting overall statistics:")
        stats = komoditi_service.get_statistics()
        print(f"   Total records: {stats['total_records']}")
        print(f"   Total harga: {stats['total_harga']:,.2f}")
        print(f"   Average harga: {stats['average_harga']:,.2f}")
        print(f"   Min harga: {stats['min_harga']:,.2f}")
        print(f"   Max harga: {stats['max_harga']:,.2f}")
        print(f"   Unique codes: {stats['unique_kode']}")
        print(f"   Unique units: {stats['unique_satuan']}")
        print()
        
        # 9. Get by date range
        print("9. Getting commodities by date range (last 30 days):")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range_data = komoditi_service.get_by_date_range(start_date, end_date, skip=0, limit=5)
        print(f"   Found {len(date_range_data)} records in the last 30 days")
        for record in date_range_data[:2]:
            print(f"   - ID: {record.id}, Created: {record.created_at}, Name: {record.nama_komoditi}")
        print()
        
        # 10. Get commodities by specific unit
        print("10. Getting commodities by specific unit (example: 'TON'):")
        unit_specific_data = komoditi_service.get_komoditi_by_unit("TON", skip=0, limit=5)
        print(f"   Found {len(unit_specific_data)} records with unit 'TON'")
        for record in unit_specific_data[:2]:
            print(f"   - ID: {record.id}, Name: {record.nama_komoditi}, Price: {record.harga_komoditi}")
        print()
        
    except Exception as e:
        print(f"Error during queries: {e}")
    finally:
        db.close()

def create_sample_data():
    """Create sample commodity data for testing"""
    
    db: Session = SessionLocal()
    komoditi_service = KomoditiService(db)
    
    try:
        # Sample data
        sample_records = [
            KomoditiCreate(
                kode_komoditi="K001",
                nama_komoditi="Beras Premium",
                harga_komoditi=Decimal("15000"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K002",
                nama_komoditi="Gula Pasir",
                harga_komoditi=Decimal("12000"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K003",
                nama_komoditi="Minyak Goreng",
                harga_komoditi=Decimal("18000"),
                satuan_komoditi="LITER"
            ),
            KomoditiCreate(
                kode_komoditi="K004",
                nama_komoditi="Tepung Terigu",
                harga_komoditi=Decimal("8000"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K005",
                nama_komoditi="Kopi Robusta",
                harga_komoditi=Decimal("25000"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K006",
                nama_komoditi="Karet",
                harga_komoditi=Decimal("45000"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K007",
                nama_komoditi="Kelapa Sawit",
                harga_komoditi=Decimal("3500"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K008",
                nama_komoditi="Kakao",
                harga_komoditi=Decimal("28000"),
                satuan_komoditi="KG"
            ),
            KomoditiCreate(
                kode_komoditi="K009",
                nama_komoditi="Tembaga",
                harga_komoditi=Decimal("85000"),
                satuan_komoditi="TON"
            ),
            KomoditiCreate(
                kode_komoditi="K010",
                nama_komoditi="Nikel",
                harga_komoditi=Decimal("120000"),
                satuan_komoditi="TON"
            )
        ]
        
        print("Creating sample commodity data...")
        for record in sample_records:
            created = komoditi_service.create(record)
            print(f"Created commodity with ID: {created.id} - {created.nama_komoditi}")
        
        print("Sample commodity data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Uncomment the line below to create sample data first
    # create_sample_data()
    
    # Run example queries
    example_queries() 