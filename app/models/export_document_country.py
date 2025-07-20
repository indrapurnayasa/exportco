from sqlalchemy import Column, String, Text
from app.db.database import Base

class ExportDocumentCountry(Base):
    __tablename__ = "export_document_country"

    id = Column(String, primary_key=True)
    country_name = Column(Text, nullable=False)
    id_doc = Column(String, nullable=True)
    document_name = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    country_code = Column(String(2), nullable=False) 