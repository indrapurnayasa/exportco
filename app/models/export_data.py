from sqlalchemy import Column, String, Numeric, Text, DateTime, Index
from sqlalchemy.sql import func
from app.db.database import Base

class ExportData(Base):
    __tablename__ = "export_data"
    
    id = Column(String(20), primary_key=True, server_default="nextval('export_data_id_seq'::regclass)")
    provorig = Column(String(10), nullable=True)
    value = Column(Numeric, nullable=True)
    netweight = Column(Numeric, nullable=True)
    kodehs = Column(Text, nullable=True)
    pod = Column(Text, nullable=True)
    ctr = Column(Text, nullable=True)
    tahun = Column(String(6), nullable=True)
    bulan = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=True)
    ctr_code = Column(String(2), nullable=True)
    comodity_code = Column(String(10), nullable=True)
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_export_data_tahun_bulan', 'tahun', 'bulan'),
        Index('idx_export_data_comodity_code', 'comodity_code'),
        Index('idx_export_data_ctr_code', 'ctr_code'),
        Index('idx_export_data_netweight', 'netweight'),
        Index('idx_export_data_tahun_comodity', 'tahun', 'comodity_code'),
        Index('idx_export_data_created_at', 'created_at'),
    )