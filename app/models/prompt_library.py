from sqlalchemy import Column, Integer, Text, Boolean, DateTime, func
from app.db.database import Base

class PromptLibrary(Base):
    __tablename__ = "prompt_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_template = Column(Text, nullable=False)
    keywords = Column(Text, nullable=True)  # Store as JSON string for compatibility
    embedding = Column(Text, nullable=True)  # Store as JSON string for compatibility
    usage_count = Column(Integer, default=0, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True) 