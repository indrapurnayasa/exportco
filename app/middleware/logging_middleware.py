import time
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from app.utils.logger import log_api_request

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Log the request asynchronously (don't await to avoid blocking)
        try:
            await log_api_request(request, response, process_time)
        except Exception as e:
            # Don't let logging errors affect the response
            pass
        
        return response 