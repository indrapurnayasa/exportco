from sqlalchemy import Column, Text, DateTime, func, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import text as sa_text
from app.db.database import Base
import uuid

class ExportDutyChunk(Base):
    __tablename__ = "export_duty_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # Store as JSON string for compatibility
    metadata_doc = Column(Text, nullable=True)  # Store as JSON string for compatibility
    created_at = Column(DateTime, server_default=func.now(), nullable=True) 