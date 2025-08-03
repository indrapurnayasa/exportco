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

# Initialize Redis client (global, outside endpoint)
redis_client = redis.Redis.from_url("redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884")

# Use the new Redis configuration for logging
log_redis = redis.Redis.from_url("redis://default:ENRwPubGW1VmpdNmr5kSJG7jqW7IdyKG@redis-16098.crce185.ap-seast-1-1.ec2.redns.redis-cloud.com:16098")

class ChatbotQuery(BaseModel):
    query: str
    session_id: str = None  # Optional session ID for conversation continuity

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
            history_key = f"chatbot_history:{session_id}"
            history_data = redis_client.get(history_key)
            if history_data:
                conversation_history = json.loads(history_data)
        
        # Create context-aware query
        context_query = payload.query
        if conversation_history:
            # Add recent conversation context (last 3 exchanges)
            recent_context = conversation_history[-6:]  # Last 3 Q&A pairs
            context_parts = []
            for exchange in recent_context:
                context_parts.append(f"User: {exchange.get('user_query', '')}")
                context_parts.append(f"Assistant: {exchange.get('assistant_response', '')}")
            context_query = f"Previous conversation:\n" + "\n".join(context_parts) + f"\n\nCurrent question: {payload.query}"
        
        cache_key = f"chatbot:{context_query}"
        cached = redis_client.get(cache_key)
        if cached:
            response = json.loads(cached)
            # Update conversation history
            conversation_history.append({
                "user_query": payload.query,
                "assistant_response": response.get("answer", ""),
                "timestamp": time.time()
            })
            # Store updated history
            history_key = f"chatbot_history:{session_id}"
            redis_client.set(history_key, json.dumps(conversation_history), ex=3600)  # 1 hour expiry
            
            # Log the response to Redis log DB
            log_key = f"chatbotlog:{int(time.time())}:{random.randint(1000,9999)}"
            log_redis.set(log_key, json.dumps(response), ex=1800)
            return response

        # Use optimized chatbot service with context
        optimized_service = OptimizedChatbotService(db)
        result = await optimized_service.process_chatbot_query(context_query)

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
        history_key = f"chatbot_history:{session_id}"
        redis_client.set(history_key, json.dumps(conversation_history), ex=3600)  # 1 hour expiry
        
        # Cache the result (as JSON string, set expiration to 1 hour)
        redis_client.set(cache_key, json.dumps(result), ex=3600)
        # Log the response to Redis log DB
        log_key = f"chatbotlog:{int(time.time())}:{random.randint(1000,9999)}"
        log_redis.set(log_key, json.dumps(result), ex=1800)
        
        # Add session_id to response
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
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error clearing conversation history: {str(e)}") 