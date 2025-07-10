from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PromptLibraryBase(BaseModel):
    prompt_template: str
    keywords: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    usage_count: Optional[int] = 0
    is_active: Optional[bool] = True

class PromptLibraryCreate(PromptLibraryBase):
    pass

class PromptLibraryUpdate(BaseModel):
    prompt_template: Optional[str] = None
    keywords: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    usage_count: Optional[int] = None
    is_active: Optional[bool] = None

class PromptLibraryResponse(PromptLibraryBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 