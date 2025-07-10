from sqlalchemy import Column, Integer, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.database import Base
from pgvector.sqlalchemy import Vector

class PromptLibrary(Base):
    __tablename__ = "prompt_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_template = Column(Text, nullable=False)
    keywords = Column(ARRAY(Text), nullable=True)
    embedding = Column(Vector(1536), nullable=True)  # Adjust dimension if needed
    usage_count = Column(Integer, default=0, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True) 