from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, update, text
from sqlalchemy.orm import selectinload
from pgvector.sqlalchemy import Vector
from typing import List, Optional, Tuple
import json
from app.models.prompt_library import PromptLibrary
from app.schemas.prompt_library import PromptLibraryCreate, PromptLibraryUpdate
import numpy as np
import asyncio
import logging
from datetime import datetime
import os
import openai

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
            # Guard against missing/empty query embeddings
            if not query_embedding:
                return None
            
            # Simple approach: get all active prompts and calculate similarity in Python
            query = select(PromptLibrary).where(PromptLibrary.is_active == True)
            result = await self.db.execute(query)
            prompts = result.scalars().all()
            
            if not prompts:
                return None
            
            # Calculate similarity for each prompt
            best_prompt = None
            best_similarity = -1.0
            
            for prompt in prompts:
                if prompt.embedding is None:
                    continue
                
                # Parse embedding if stored as JSON string, pgvector text, or other iterable
                try:
                    embedding_value = prompt.embedding
                    if isinstance(embedding_value, str):
                        # Try JSON first (e.g., "[0.1, ...]")
                        parsed = None
                        try:
                            parsed = json.loads(embedding_value)
                        except Exception:
                            parsed = None
                        # If not JSON, try to parse bracketed list format
                        if parsed is None and embedding_value.strip().startswith("[") and embedding_value.strip().endswith("]"):
                            try:
                                parsed = json.loads(embedding_value.strip())
                            except Exception:
                                parsed = None
                        embedding_value = parsed if parsed is not None else embedding_value
                    # Convert memoryview/bytes-like to list of floats when possible
                    if not isinstance(embedding_value, list) and hasattr(embedding_value, "__iter__"):
                        try:
                            embedding_value = list(embedding_value)
                        except Exception:
                            pass
                except Exception:
                    # Skip prompts with invalid embeddings
                    continue
                
                if not isinstance(embedding_value, list) or not embedding_value:
                    continue
                
                # Calculate cosine similarity
                import numpy as np
                prompt_vector = np.array(embedding_value, dtype=float)
                query_vector = np.array(query_embedding, dtype=float)
                
                # Normalize vectors
                prompt_norm = np.linalg.norm(prompt_vector)
                query_norm = np.linalg.norm(query_vector)
                
                if prompt_norm > 0 and query_norm > 0 and prompt_vector.shape == query_vector.shape:
                    similarity = float(np.dot(prompt_vector, query_vector) / (prompt_norm * query_norm))
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_prompt = prompt
            
            if best_prompt is not None:
                logger.info(f"[SIMILARITY SEARCH] Best prompt {best_prompt.id} with similarity: {best_similarity:.3f}")
                # Respect the threshold: treat too-low cosine as no match so caller can fallback
                if best_similarity < float(threshold):
                    return None
                return best_prompt, max(best_similarity, 0.0)

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

    def _safe_parse_keywords(self, keywords_value) -> Optional[List[str]]:
        try:
            if isinstance(keywords_value, list):
                return [str(k) for k in keywords_value]
            if isinstance(keywords_value, str):
                raw = keywords_value.strip()
                if raw.startswith("{") and raw.endswith("}"):
                    inner = raw[1:-1]
                    return [p.strip().strip('"') for p in inner.split(',') if p.strip()]
                return list(json.loads(raw))
        except Exception:
            return None
        return None

    async def get_best_prompt_blended(self, query_embedding: List[float], query_text: Optional[str]) -> Optional[Tuple[PromptLibrary, float]]:
        """
        Blended prompt selection using cosine similarity on embeddings and keyword relevance.
        Returns (prompt, blended_score in [0,1]).
        """
        try:
            if not query_text and not query_embedding:
                return None

            text_lower = (query_text or "").lower()
            prompts = await self.get_active_prompts()
            if not prompts:
                return None

            best_prompt: Optional[PromptLibrary] = None
            best_score: float = -1.0

            # Prepare numpy vector for query embedding
            query_vec = None
            if query_embedding:
                try:
                    query_vec = np.array(query_embedding, dtype=float)
                except Exception:
                    query_vec = None

            for prompt in prompts:
                # Cosine similarity part
                cosine = 0.0
                if query_vec is not None and getattr(prompt, "embedding", None) is not None:
                    try:
                        emb_val = prompt.embedding
                        if isinstance(emb_val, str):
                            try:
                                emb_val = json.loads(emb_val)
                            except Exception:
                                # Try bracketed list string
                                if emb_val.strip().startswith("[") and emb_val.strip().endswith("]"):
                                    emb_val = json.loads(emb_val)
                        if isinstance(emb_val, list) and len(emb_val) == query_vec.shape[0]:
                            pvec = np.array(emb_val, dtype=float)
                            denom = (np.linalg.norm(pvec) * np.linalg.norm(query_vec))
                            if denom > 0:
                                cosine = float(np.dot(pvec, query_vec) / denom)
                    except Exception:
                        cosine = 0.0

                # Keyword relevance part
                keyword_score = 0.0
                if text_lower:
                    kws = self._safe_parse_keywords(getattr(prompt, "keywords", None))
                    if isinstance(kws, list) and kws:
                        matches = sum(1 for kw in kws if isinstance(kw, str) and kw.lower() in text_lower)
                        # Normalize: 0 to 1 with diminishing returns
                        keyword_score = min(1.0, matches / 3.0)

                # Blended score: favor embeddings, keep keywords as secondary signal
                blended = 0.8 * max(0.0, cosine) + 0.2 * keyword_score

                if blended > best_score:
                    best_score = blended
                    best_prompt = prompt

            if best_prompt is None:
                return None

            # Require minimum plausibility: either cosine moderately high or blended high
            if best_score < 0.55:
                # Too uncertain; let caller fallback
                return None

            return best_prompt, float(best_score)
        except Exception as e:
            logger.error(f"Error in get_best_prompt_blended: {e}")
            return None
    async def get_best_prompt_by_keywords(self, query_text: str) -> Optional[Tuple[PromptLibrary, float]]:
        """
        Fallback prompt selection using keyword matching when embeddings are missing or invalid.
        Returns a tuple of (prompt, heuristic_similarity in [0.0, 1.0]).
        """
        try:
            text_lower = (query_text or "").lower()
            prompts = await self.get_active_prompts()
            if not prompts:
                return None

            best_prompt: Optional[PromptLibrary] = None
            best_score: float = -1.0

            for prompt in prompts:
                # Parse keywords stored as JSON string in Text column, if any
                keywords_value = getattr(prompt, "keywords", None)
                keywords = None
                try:
                    if isinstance(keywords_value, list):
                        keywords = keywords_value
                    elif isinstance(keywords_value, str):
                        raw = keywords_value.strip()
                        # Handle Postgres array syntax: {a,b,c}
                        if raw.startswith("{") and raw.endswith("}"):
                            inner = raw[1:-1]
                            # split by comma, strip quotes/braces/spaces
                            if inner:
                                parts = [p.strip().strip('"') for p in inner.split(',')]
                                keywords = [p for p in parts if p]
                            else:
                                keywords = []
                        else:
                            # Try JSON array
                            keywords = json.loads(raw)
                    else:
                        keywords = None
                except Exception:
                    keywords = None

                if not isinstance(keywords, list) or not keywords:
                    # No keywords; very low score
                    score = 0.0
                else:
                    matches = sum(1 for kw in keywords if isinstance(kw, str) and kw.lower() in text_lower)
                    # Heuristic scoring: base 0.5 + 0.1 per match, capped at 0.95
                    score = min(0.95, 0.5 + 0.1 * matches) if matches > 0 else 0.0

                if score > best_score:
                    best_score = score
                    best_prompt = prompt

            if best_prompt is None:
                return None

            return best_prompt, max(0.0, float(best_score))
        except Exception as e:
            logger.error(f"Error in get_best_prompt_by_keywords: {e}")
            return None

    async def batch_create_embeddings(self, prompts: List[PromptLibrary]) -> None:
        """
        Batch create embeddings for multiple prompts
        """
        # Deprecated: prefer backfill_embeddings which queries prompts internally
        await self.backfill_embeddings()

    async def backfill_embeddings(self, model: str = "text-embedding-3-small", force: bool = False) -> int:
        """
        Create embeddings for active prompts that are missing or have invalid embeddings.
        Returns the number of prompts updated.
        """
        updated_count = 0
        try:
            # Fetch active prompts
            query = select(PromptLibrary).where(PromptLibrary.is_active == True)
            result = await self.db.execute(query)
            prompts = result.scalars().all()

            if not prompts:
                return 0

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            for prompt in prompts:
                needs_embedding = force
                if not needs_embedding:
                    if prompt.embedding is None:
                        needs_embedding = True
                    else:
                        try:
                            embedded_value = prompt.embedding
                            if isinstance(embedded_value, str):
                                embedded_value = json.loads(embedded_value)
                            if not isinstance(embedded_value, list) or len(embedded_value) == 0:
                                needs_embedding = True
                        except Exception:
                            needs_embedding = True

                if not needs_embedding:
                    continue

                # Choose concise embedding text: prefer keywords; else trimmed template
                try:
                    # Build embedding input
                    embed_input = None
                    # Try parse keywords similarly to keyword fallback
                    keywords_value = getattr(prompt, "keywords", None)
                    try:
                        if isinstance(keywords_value, list):
                            kws = keywords_value
                        elif isinstance(keywords_value, str):
                            raw = keywords_value.strip()
                            if raw.startswith("{") and raw.endswith("}"):
                                inner = raw[1:-1]
                                kws = [p.strip().strip('"') for p in inner.split(',') if p.strip()]
                            else:
                                kws = json.loads(raw)
                        else:
                            kws = None
                    except Exception:
                        kws = None

                    if isinstance(kws, list) and kws:
                        embed_input = ", ".join(str(k) for k in kws)
                    else:
                        text_src = prompt.prompt_template or ""
                        # Trim to first 512 chars to keep embedding focused
                        embed_input = text_src[:512]

                    response = await asyncio.to_thread(
                        client.embeddings.create,
                        input=embed_input,
                        model=model
                    )
                    vector = response.data[0].embedding
                    # Prefer storing into pgvector column using explicit cast
                    try:
                        vector_str = "[" + ",".join(str(float(x)) for x in vector) + "]"
                        await self.db.execute(
                            text("UPDATE prompt_library SET embedding = :vec::vector, updated_at = now() WHERE id = :id"),
                            {"vec": vector_str, "id": prompt.id}
                        )
                    except Exception:
                        # Fallback to storing JSON text if column is textual
                        prompt.embedding = json.dumps(vector)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to embed prompt {prompt.id}: {e}")
                    continue

            if updated_count > 0:
                await self.db.commit()

            return updated_count
        except Exception as e:
            logger.error(f"Error during backfill_embeddings: {e}")
            return updated_count