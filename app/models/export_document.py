from sqlalchemy import Column, String, Text
from app.db.database import Base

class ExportDocument(Base):
    __tablename__ = "export_document"

    id_doc = Column(String, primary_key=True)
    nama_dokumen = Column(Text, nullable=False)
    template_dokumen = Column(Text, nullable=False) 