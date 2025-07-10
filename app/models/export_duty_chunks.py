from sqlalchemy import Column, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import text as sa_text
from app.db.database import Base
from pgvector.sqlalchemy import Vector
import uuid

class ExportDutyChunk(Base):
    __tablename__ = "export_duty_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text('uuid_generate_v4()'))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # adjust dimension if needed
    metadata_doc = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True) 