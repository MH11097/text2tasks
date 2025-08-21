import logging
import json
import sys
import os
from datetime import datetime
from typing import Any, Dict
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

from shared.config.settings import settings


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""
    
    def filter(self, record):
        # Add request ID if available (will be set by middleware)
        if not hasattr(record, 'request_id'):
            record.request_id = None
        if not hasattr(record, 'user_id'):
            record.user_id = None
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add service info
        log_record['service'] = 'ai-work-os'
        log_record['version'] = '1.0.0'
        
        # Add level name
        log_record['level'] = record.levelname
        
        # Add request context if available
        if hasattr(record, 'request_id') and record.request_id:
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id') and record.user_id:
            log_record['user_id'] = record.user_id


def setup_logging():
    """Configure structured logging for the application."""
    
    # Ensure logs directory exists
    log_dir = "logs/backend"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create JSON formatter
    json_formatter = CustomJsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Console handler (for development)
    if settings.debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(console_handler)
    
    # File handlers with rotation
    # Main application log
    app_handler = RotatingFileHandler(
        filename=f"{log_dir}/app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setFormatter(json_formatter)
    app_handler.addFilter(RequestContextFilter())
    app_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    
    # Error log
    error_handler = RotatingFileHandler(
        filename=f"{log_dir}/error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setFormatter(json_formatter)
    error_handler.addFilter(RequestContextFilter())
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Debug log (only in debug mode)
    if settings.debug:
        debug_handler = RotatingFileHandler(
            filename=f"{log_dir}/debug.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        debug_handler.setFormatter(json_formatter)
        debug_handler.addFilter(RequestContextFilter())
        debug_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(debug_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    
    # Log startup message
    root_logger.info("Logging system initialized", extra={
        "log_dir": log_dir,
        "debug_mode": settings.debug,
        "handlers": len(root_logger.handlers)
    })
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)