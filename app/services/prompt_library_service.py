from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, update
from sqlalchemy.orm import selectinload
from pgvector.sqlalchemy import Vector
from typing import List, Optional, Tuple
from app.models.prompt_library import PromptLibrary
from app.schemas.prompt_library import PromptLibraryCreate, PromptLibraryUpdate
import numpy as np
from sqlalchemy import text
import asyncio
from functools import lru_cache
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptLibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[PromptLibrary]:
        """Get all prompts with pagination"""
        query = select(PromptLibrary).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, prompt_id: int) -> Optional[PromptLibrary]:
        """Get prompt by ID with caching"""
        cache_key = f"prompt_{prompt_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        query = select(PromptLibrary).where(PromptLibrary.id == prompt_id)
        result = await self.db.execute(query)
        prompt = result.scalar_one_or_none()
        
        if prompt:
            self._cache[cache_key] = prompt
        return prompt

    async def create(self, prompt_data: PromptLibraryCreate) -> PromptLibrary:
        """Create new prompt"""
        prompt = PromptLibrary(**prompt_data.dict())
        self.db.add(prompt)
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def update(self, prompt_id: int, prompt_data: PromptLibraryUpdate) -> Optional[PromptLibrary]:
        """Update existing prompt"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return None
        
        # Clear cache
        cache_key = f"prompt_{prompt_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        for field, value in prompt_data.dict(exclude_unset=True).items():
            setattr(prompt, field, value)
        
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def delete(self, prompt_id: int) -> bool:
        """Delete prompt"""
        prompt = await self.get_by_id(prompt_id)
        if not prompt:
            return False
        
        # Clear cache
        cache_key = f"prompt_{prompt_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        await self.db.delete(prompt)
        await self.db.commit()
        return True

    async def log_prompt_usage(self, prompt_id: int, user_query: str, similarity: float, response_type: str = "chatbot"):
        """
        Log prompt usage and update usage count
        """
        try:
            # Update usage count
            stmt = update(PromptLibrary).where(PromptLibrary.id == prompt_id).values(
                usage_count=PromptLibrary.usage_count + 1,
                updated_at=datetime.utcnow()
            )
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Clear cache for this prompt
            cache_key = f"prompt_{prompt_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            # Log the usage
            logger.info(f"[PROMPT USAGE] Prompt ID: {prompt_id}, Query: '{user_query[:100]}...', Similarity: {similarity:.3f}, Type: {response_type}")
            
            # You can also log to a separate table if needed
            # await self._log_to_usage_table(prompt_id, user_query, similarity, response_type)
            
        except Exception as e:
            logger.error(f"Error logging prompt usage: {e}")

    async def get_most_similar_prompt_optimized(self, query_embedding: List[float], threshold: float = 0.7) -> Optional[Tuple[PromptLibrary, float]]:
        """
        Optimized similarity search with caching and reduced database queries
        """
        try:
            # Simple approach: get all active prompts and calculate similarity in Python
            query = select(PromptLibrary).where(PromptLibrary.is_active == True)
            result = await self.db.execute(query)
            prompts = result.scalars().all()
            
            if not prompts:
                return None
            
            # Calculate similarity for each prompt
            best_prompt = None
            best_similarity = 0.0
            
            for prompt in prompts:
                if prompt.embedding is not None:
                    # Calculate cosine similarity
                    import numpy as np
                    prompt_vector = np.array(prompt.embedding)
                    query_vector = np.array(query_embedding)
                    
                    # Normalize vectors
                    prompt_norm = np.linalg.norm(prompt_vector)
                    query_norm = np.linalg.norm(query_vector)
                    
                    if prompt_norm > 0 and query_norm > 0:
                        similarity = np.dot(prompt_vector, query_vector) / (prompt_norm * query_norm)
                        
                        if similarity > best_similarity and similarity >= threshold:
                            best_similarity = similarity
                            best_prompt = prompt
            
            if best_prompt:
                logger.info(f"[SIMILARITY SEARCH] Found prompt {best_prompt.id} with similarity: {best_similarity:.3f}")
                return best_prompt, best_similarity

            return None

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return None

    async def get_most_similar_prompt(self, query_embedding: List[float], threshold: float = 0.7) -> Optional[Tuple[PromptLibrary, float]]:
        """
        Get most similar prompt using vector similarity search
        """
        return await self.get_most_similar_prompt_optimized(query_embedding, threshold)

    async def get_active_prompts(self) -> List[PromptLibrary]:
        """Get all active prompts with caching"""
        cache_key = "active_prompts"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        query = select(PromptLibrary).where(PromptLibrary.is_active == True)
        result = await self.db.execute(query)
        prompts = result.scalars().all()
        
        self._cache[cache_key] = prompts
        return prompts

    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()

    async def batch_create_embeddings(self, prompts: List[PromptLibrary]) -> None:
        """
        Batch create embeddings for multiple prompts
        """
        # This would be implemented if we need to create embeddings in bulk
        pass 