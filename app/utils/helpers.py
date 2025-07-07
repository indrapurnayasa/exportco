import logging
from typing import Any, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_datetime(dt: datetime) -> str:
    """Format datetime to string"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def log_request_info(request_data: Dict[str, Any]) -> None:
    """Log request information"""
    logger.info(f"Request data: {request_data}")

def validate_email_format(email: str) -> bool:
    """Simple email validation"""
    return "@" in email and "." in email

def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    return text.lower().replace(" ", "-").replace("_", "-") 