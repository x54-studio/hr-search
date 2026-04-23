"""
Custom exception classes for the Search application.

This module defines a hierarchy of custom exceptions that provide
structured error handling with consistent formatting and context.
"""

import time
from typing import Any, Dict, Optional


class SearchException(Exception):
    """
    Base exception class for all Search application errors.

    Provides structured error information with:
    - Error code for programmatic handling
    - Human-readable message
    - Additional context in details
    - Timestamp and request ID for tracing
    """

    def __init__(
        self,
        message: str,
        error_code: str = "SEARCH_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id
        self.cause = cause
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
        }
    
    def __str__(self) -> str:
        """String representation of the exception."""
        return f"{self.error_code}: {self.message}"


class ValidationError(SearchException):
    """
    Exception raised for input validation errors.
    
    Maps to HTTP 400 Bad Request status code.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        details = {}
        if field is not None:
            details["field"] = field
        if value is not None:
            details["value"] = value
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            request_id=request_id,
        )


class SearchError(SearchException):
    """
    Exception raised for search-related errors.
    
    Maps to HTTP 500/503 status codes depending on error type.
    """
    
    def __init__(
        self,
        message: str,
        search_type: Optional[str] = None,
        query: Optional[str] = None,
        request_id: Optional[str] = None,
        cause: Optional[Exception] = None,
        **kwargs,
    ):
        details = {"search_type": search_type or "unknown"}
        if query is not None:
            details["query"] = query
        details.update(kwargs)
        
        super().__init__(
            message=message,
            error_code="SEARCH_ERROR",
            details=details,
            request_id=request_id,
            cause=cause,
        )


class ResourceNotFoundError(SearchException):
    """
    Exception raised when a requested resource is not found.
    
    Maps to HTTP 404 Not Found status code.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        details = {}
        if resource_type is not None:
            details["resource_type"] = resource_type
        if resource_id is not None:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
            request_id=request_id,
        )


class ConfigurationError(SearchException):
    """
    Exception raised for configuration-related errors.
    
    Maps to HTTP 500 Internal Server Error status code.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        request_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        details = {}
        if config_key is not None:
            details["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            request_id=request_id,
            cause=cause,
        )
