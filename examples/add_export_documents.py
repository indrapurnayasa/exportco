"""
Script untuk menambahkan sample data dokumen ekspor ke database
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models.export_document_country import ExportDocumentCountry
from app.models.export_document import ExportDocument
from sqlalchemy import select
import uuid

async def add_export_documents():
    """Add sample export document data"""
    
    # Sample export document country data
    export_document_country_data = [
        {
            "id": "doc_india_001",
            "country_name": "India",
            "id_doc": "template_invoice",
            "document_name": "Commercial Invoice",
            "source": "Exporter",
            "country_code": "IN"
        },
        {
            "id": "doc_india_002", 
            "country_name": "India",
            "id_doc": "template_packing",
            "document_name": "Packing List",
            "source": "Exporter",
            "country_code": "IN"
        },
        {
            "id": "doc_india_003",
            "country_name": "India",
            "id_doc": None,
            "document_name": "Certificate of Origin",
            "source": "Chamber of Commerce",
            "country_code": "IN"
        },
        {
            "id": "doc_china_001",
            "country_name": "China",
            "id_doc": "template_invoice",
            "document_name": "Commercial Invoice",
            "source": "Exporter",
            "country_code": "CN"
        },
        {
            "id": "doc_china_002",
            "country_name": "China",
            "id_doc": None,
            "document_name": "Phytosanitary Certificate",
            "source": "Ministry of Agriculture",
            "country_code": "CN"
        },
        {
            "id": "doc_bangladesh_001",
            "country_name": "Bangladesh",
            "id_doc": "template_invoice",
            "document_name": "Commercial Invoice",
            "source": "Exporter",
            "country_code": "BD"
        },
        {
            "id": "doc_bangladesh_002",
            "country_name": "Bangladesh",
            "id_doc": None,
            "document_name": "Import License",
            "source": "Bangladesh Import Authority",
            "country_code": "BD"
        }
    ]
    
    # Sample export document templates
    export_document_templates = [
        {
            "id_doc": "template_invoice",
            "nama_dokumen": "Commercial Invoice Template",
            "template_dokumen": """
<!DOCTYPE html>
<html>
<head>
    <title>Commercial Invoice</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; }
        .section { margin: 20px 0; }
        .row { display: flex; margin: 5px 0; }
        .label { font-weight: bold; width: 150px; }
        .value { flex: 1; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #000; padding: 8px; text-align: left; }
        th { background-color: #f0f0f0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>COMMERCIAL INVOICE</h1>
        <p>Invoice No: {{nomor_invoice}} | Date: {{tanggal}}</p>
    </div>
    
    <div class="section">
        <div class="row">
            <div class="label">Exporter:</div>
            <div class="value">{{nama_eksportir}}</div>
        </div>
        <div class="row">
            <div class="label">Address:</div>
            <div class="value">{{alamat_eksportir}}</div>
        </div>
        <div class="row">
            <div class="label">Country:</div>
            <div class="value">{{negara_asal}}</div>
        </div>
    </div>
    
    <div class="section">
        <div class="row">
            <div class="label">Importer:</div>
            <div class="value">{{nama_importir}}</div>
        </div>
        <div class="row">
            <div class="label">Address:</div>
            <div class="value">{{alamat_importir}}</div>
        </div>
        <div class="row">
            <div class="label">Country:</div>
            <div class="value">{{negara_tujuan}}</div>
        </div>
    </div>
    
    <div class="section">
        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit Price (USD)</th>
                    <th>Total (USD)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>{{nama_produk}}</td>
                    <td>{{kuantitas}} {{satuan}}</td>
                    <td>{{harga_satuan}}</td>
                    <td>{{total_harga}}</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <div class="row">
            <div class="label">Total Amount:</div>
            <div class="value">USD {{total_amount}}</div>
        </div>
        <div class="row">
            <div class="label">Terms of Payment:</div>
            <div class="value">{{terms_payment}}</div>
        </div>
    </div>
</body>
</html>
            """
        },
        {
            "id_doc": "template_packing",
            "nama_dokumen": "Packing List Template", 
            "template_dokumen": """
<!DOCTYPE html>
<html>
<head>
    <title>Packing List</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; }
        .section { margin: 20px 0; }
        .row { display: flex; margin: 5px 0; }
        .label { font-weight: bold; width: 150px; }
        .value { flex: 1; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #000; padding: 8px; text-align: left; }
        th { background-color: #f0f0f0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PACKING LIST</h1>
        <p>Date: {{tanggal}}</p>
    </div>
    
    <div class="section">
        <div class="row">
            <div class="label">Exporter:</div>
            <div class="value">{{nama_eksportir}}</div>
        </div>
        <div class="row">
            <div class="label">Importer:</div>
            <div class="value">{{nama_importir}}</div>
        </div>
    </div>
    
    <div class="section">
        <table>
            <thead>
                <tr>
                    <th>Package No</th>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Weight (kg)</th>
                    <th>Dimensions (cm)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{{nomor_package}}</td>
                    <td>{{nama_produk}}</td>
                    <td>{{kuantitas}} {{satuan}}</td>
                    <td>{{berat}}</td>
                    <td>{{dimensi}}</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <div class="row">
            <div class="label">Total Packages:</div>
            <div class="value">{{total_packages}}</div>
        </div>
        <div class="row">
            <div class="label">Total Weight:</div>
            <div class="value">{{total_weight}} kg</div>
        </div>
    </div>
</body>
</html>
            """
        }
    ]
    
    try:
        # Get database session
        async for db in get_async_db():
            try:
                # Check if export document country data already exists
                result = await db.execute(select(ExportDocumentCountry))
                existing_docs = result.scalars().all()
                
                if existing_docs:
                    print(f"✅ Export document country data already exists ({len(existing_docs)} records)")
                    print("   Sample records:")
                    for doc in existing_docs[:3]:
                        print(f"   - {doc.country_name}: {doc.document_name}")
                    return
                
                # Add export document country data
                for doc_data in export_document_country_data:
                    new_doc = ExportDocumentCountry(
                        id=doc_data["id"],
                        country_name=doc_data["country_name"],
                        id_doc=doc_data["id_doc"],
                        document_name=doc_data["document_name"],
                        source=doc_data["source"],
                        country_code=doc_data["country_code"]
                    )
                    db.add(new_doc)
                
                # Add export document templates
                for template_data in export_document_templates:
                    new_template = ExportDocument(
                        id_doc=template_data["id_doc"],
                        nama_dokumen=template_data["nama_dokumen"],
                        template_dokumen=template_data["template_dokumen"]
                    )
                    db.add(new_template)
                
                await db.commit()
                
                print(f"✅ Berhasil menambahkan {len(export_document_country_data)} export document records")
                print(f"✅ Berhasil menambahkan {len(export_document_templates)} document templates")
                print("   Sample data added:")
                for doc_data in export_document_country_data[:3]:
                    print(f"   - {doc_data['country_name']}: {doc_data['document_name']}")
                
            except Exception as e:
                print(f"❌ Error adding export documents: {e}")
                await db.rollback()
            finally:
                await db.close()
                break
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    print("🔄 Adding export document data to database...")
    asyncio.run(add_export_documents())
    print("✅ Done!") 