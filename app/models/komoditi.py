from sqlalchemy import Column, String, Numeric, Text, DateTime, Date, Index
from sqlalchemy.sql import func
from app.db.database import Base

class Komoditi(Base):
    __tablename__ = "komoditi"
    
    id = Column(String(10), primary_key=True, server_default="substring(replace(uuid_generate_v4()::text, '-', ''), 1, 10)")
    kode_komoditi = Column(String(10), nullable=False)
    nama_komoditi = Column(Text, nullable=False)
    harga_komoditi = Column(Numeric, nullable=False)
    tanggal_harga = Column(Date, nullable=True)  # Date when the price was recorded
    satuan_komoditi = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=True)
