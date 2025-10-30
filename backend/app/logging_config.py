"""
Logging configuration for HR Search application.

This module provides structured logging with request ID tracking,
consistent formatting, and proper log levels for different environments.
"""

import logging
import logging.config
import os
import sys
from contextvars import ContextVar
from typing import Any, Dict, Optional
from pathlib import Path

# Context variable for request ID tracking
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    structured_logging: bool = True,
) -> logging.Logger:
    """
    Setup application logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        structured_logging: Whether to use structured logging format
    
    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Base logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
            "structured": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, "name": "%(name)s", "msg": "%(message)s", "args": [], "levelname": "%(levelname)s", "levelno": %(levelno)d, "pathname": "%(pathname)s", "filename": "%(filename)s", "exc_info": null, "exc_text": null, "stack_info": null, "lineno": %(lineno)d, "funcName": "%(funcName)s", "created": %(created)f, "msecs": %(msecs)d, "relativeCreated": %(relativeCreated)f, "thread": %(thread)d, "threadName": "%(threadName)s", "processName": "%(processName)s", "process": %(process)d}',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured" if structured_logging else "detailed",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "hr_search": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    }
    
    # Add file handler if log_file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "structured" if structured_logging else "detailed",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
        
        # Add file handler to all loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Get and return the main logger
    logger = logging.getLogger("hr_search")
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "structured_logging": structured_logging,
        }
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (usually module name)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"hr_search.{name}")


def set_request_id(request_id: str) -> None:
    """
    Set the current request ID in context.
    
    Args:
        request_id: Unique request identifier
    """
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.
    
    Returns:
        Current request ID or None if not set
    """
    return _request_id.get()


class LoggingMixin:
    """
    Mixin class that provides logging methods to service classes.
    
    This mixin adds structured logging capabilities with automatic
    request ID inclusion and consistent formatting.
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an info message with optional extra context.
        
        Args:
            message: Log message
            extra: Additional context to include in log
        """
        log_extra = extra or {}
        request_id = get_request_id()
        if request_id:
            log_extra["request_id"] = request_id
        
        self.logger.info(message, extra=log_extra)
    
    def log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a warning message with optional extra context.
        
        Args:
            message: Log message
            extra: Additional context to include in log
        """
        log_extra = extra or {}
        request_id = get_request_id()
        if request_id:
            log_extra["request_id"] = request_id
        
        self.logger.warning(message, extra=log_extra)
    
    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an error message with optional exception and context.
        
        Args:
            message: Log message
            exception: Optional exception to log
            extra: Additional context to include in log
        """
        log_extra = extra or {}
        request_id = get_request_id()
        if request_id:
            log_extra["request_id"] = request_id
        
        if exception:
            self.logger.error(message, exc_info=exception, extra=log_extra)
        else:
            self.logger.error(message, extra=log_extra)
    
    def log_debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a debug message with optional extra context.
        
        Args:
            message: Log message
            extra: Additional context to include in log
        """
        log_extra = extra or {}
        request_id = get_request_id()
        if request_id:
            log_extra["request_id"] = request_id
        
        self.logger.debug(message, extra=log_extra)
