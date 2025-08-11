from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.database import get_async_db
from app.services.optimized_chatbot_service import OptimizedChatbotService
from app.services.prompt_library_service import PromptLibraryService
import redis
import json
import time
import random
import traceback

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize Redis client (global, outside endpoint) with timeout settings
redis_client = redis.Redis.from_url(
    "redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884",
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30
)

# Note: We keep Redis only for conversation history, not for response caching

class ChatbotQuery(BaseModel):
    query: str
    session_id: str = None  # Optional session ID for conversation continuity
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Apa itu ekspor?",
                "session_id": "my_session_123"  # Optional: provide to continue conversation
            }
        }

@router.post("/")
async def chatbot(payload: ChatbotQuery, db: AsyncSession = Depends(get_async_db)):
    """
    Direct chatbot endpoint with optimized processing and Redis caching
    """
    try:
        # Generate session ID if not provided
        session_id = payload.session_id or f"session_{int(time.time())}_{random.randint(1000,9999)}"
        
        # Get conversation history if session exists
        conversation_history = []
        if payload.session_id:
            try:
                history_key = f"chatbot_history:{session_id}"
                history_data = redis_client.get(history_key)
                if history_data:
                    conversation_history = json.loads(history_data)
            except Exception as e:
                print(f"[REDIS] Error getting conversation history: {e}")
                conversation_history = []
        
        # Disable response caching: always compute fresh result

        # Use optimized chatbot service with context
        optimized_service = OptimizedChatbotService(db)
        
        # Detect ongoing session and forward raw query + history. The service will handle
        # relevance-based context building and topic shifts.
        is_ongoing_session = bool(payload.session_id and conversation_history)
        result = await optimized_service.process_chatbot_query(
            query=payload.query,
            suppress_intro=is_ongoing_session,
            conversation_history=conversation_history
        )
        # If this is a continued session, request the generator to suppress intros
        if payload.session_id:
            # Add a flag so downstream response uses no intro
            result["suppressIntro"] = True

        # Add prompt logging if available
        if "prompt_id" in result and result.get("cot_analysis"):
            try:
                prompt_service = PromptLibraryService(db)
                await prompt_service.log_prompt_usage(
                    prompt_id=result["prompt_id"],
                    user_query=payload.query,
                    similarity=result.get("similarity", 0.0),
                    response_type="optimized_chatbot"
                )
            except Exception as e:
                print(f"[OPTIMIZED] Error logging prompt usage: {e}")

        # Update conversation history
        conversation_history.append({
            "user_query": payload.query,
            "assistant_response": result.get("answer", ""),
            "timestamp": time.time()
        })
        # Store updated history
        try:
            history_key = f"chatbot_history:{session_id}"
            redis_client.set(history_key, json.dumps(conversation_history), ex=3600)  # 1 hour expiry
        except Exception as e:
            print(f"[REDIS] Error storing conversation history: {e}")
        
        # Do not cache responses
        
        # Add session_id to response (consistent with cached response and request schema)
        result["session_id"] = session_id
        return result

    except Exception as e:
        print(f"[OPTIMIZED] Error in chatbot endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/history/{session_id}")
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a specific session
    """
    try:
        history_key = f"chatbot_history:{session_id}"
        history_data = redis_client.get(history_key)
        
        if history_data:
            conversation_history = json.loads(history_data)
            return {
                "session_id": session_id,
                "history": conversation_history,
                "total_exchanges": len(conversation_history)
            }
        else:
            return {
                "session_id": session_id,
                "history": [],
                "total_exchanges": 0,
                "message": "No conversation history found for this session"
            }
    except Exception as e:
        print(f"[REDIS] Error getting conversation history: {e}")
        return {
            "session_id": session_id,
            "history": [],
            "total_exchanges": 0,
            "message": "Error retrieving conversation history due to Redis timeout"
        }

@router.delete("/history/{session_id}")
async def clear_conversation_history(session_id: str):
    """
    Clear conversation history for a specific session
    """
    try:
        history_key = f"chatbot_history:{session_id}"
        redis_client.delete(history_key)
        return {
            "session_id": session_id,
            "message": "Conversation history cleared successfully"
        }
    except Exception as e:
        print(f"[REDIS] Error clearing conversation history: {e}")
        return {
            "session_id": session_id,
            "message": "Error clearing conversation history due to Redis timeout"
        } 