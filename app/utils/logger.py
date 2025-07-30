import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import Request, Response
import time
import json

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name: str = "hackathon_service") -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_formatter = CustomFormatter(console_format)
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "hackathon_service.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    file_formatter = logging.Formatter(file_format)
    file_handler.setFormatter(file_formatter)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "hackathon_service_errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # API requests file handler
    api_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "api_requests.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_format = "%(asctime)s - %(message)s"
    api_formatter = logging.Formatter(api_format)
    api_handler.setFormatter(api_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

def get_api_logger() -> logging.Logger:
    """Get logger specifically for API requests"""
    logger = logging.getLogger("api_requests")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # API requests file handler
    api_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "api_requests.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_format = "%(asctime)s - %(message)s"
    api_formatter = logging.Formatter(api_format)
    api_handler.setFormatter(api_formatter)
    
    logger.addHandler(api_handler)
    return logger

async def log_api_request(request: Request, response: Response, process_time: float):
    """Log API request details"""
    logger = get_api_logger()
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get user agent
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get request method and path
    method = request.method
    path = request.url.path
    query_params = str(request.query_params) if request.query_params else ""
    
    # Get response status
    status_code = response.status_code
    
    # Format the log message
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "client_ip": client_ip,
        "method": method,
        "path": path,
        "query_params": query_params,
        "status_code": status_code,
        "process_time_ms": round(process_time * 1000, 2),
        "user_agent": user_agent
    }
    
    logger.info(json.dumps(log_data))

def log_server_startup(host: str, port: int, environment: str = "production"):
    """Log server startup information"""
    logger = setup_logger()
    
    startup_info = {
        "event": "server_startup",
        "timestamp": datetime.now().isoformat(),
        "host": host,
        "port": port,
        "environment": environment,
        "python_version": sys.version,
        "pid": os.getpid()
    }
    
    logger.info(f"🚀 Server starting up: {json.dumps(startup_info)}")
    logger.info(f"📊 Server will be available at: http://{host}:{port}")
    logger.info(f"🔍 Health check endpoint: http://{host}:{port}/health")
    logger.info(f"📚 API documentation: http://{host}:{port}/docs")

def log_server_shutdown():
    """Log server shutdown information"""
    logger = setup_logger()
    
    shutdown_info = {
        "event": "server_shutdown",
        "timestamp": datetime.now().isoformat(),
        "pid": os.getpid()
    }
    
    logger.info(f"🛑 Server shutting down: {json.dumps(shutdown_info)}")

def log_database_connection(success: bool, error: Optional[str] = None):
    """Log database connection status"""
    logger = setup_logger()
    
    if success:
        logger.info("✅ Database connection established successfully")
    else:
        logger.error(f"❌ Database connection failed: {error}")

def log_configuration_validation(success: bool, errors: Optional[list] = None):
    """Log configuration validation status"""
    logger = setup_logger()
    
    if success:
        logger.info("✅ Configuration validated successfully")
    else:
        logger.error(f"❌ Configuration validation failed: {errors}")

# Create main logger instance
logger = setup_logger() 