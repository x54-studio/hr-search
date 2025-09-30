"""
Mock responses for API testing.
"""
from typing import Dict, List, Any


def mock_search_response(results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create mock search API response."""
    if results is None:
        results = [
            {
                "id": "test-webinar-1",
                "title": "Test Webinar 1",
                "description": "Test description 1",
                "category_name": "Test Category",
                "speakers": ["Test Speaker"],
                "tags": ["test", "webinar"],
                "duration_ms": 1800000,
                "recorded_date": "2024-01-01",
                "video_url": "https://example.com/video1.mp4",
                "pdf_url": "https://example.com/slides1.pdf"
            }
        ]
    
    return {
        "results": results,
        "count": len(results)
    }


def mock_autocomplete_response(suggestions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create mock autocomplete API response."""
    if suggestions is None:
        suggestions = [
            {"suggestion": "Test Webinar", "type": "webinar"},
            {"suggestion": "Test Speaker", "type": "speaker"},
            {"suggestion": "test-tag", "type": "tag"}
        ]
    
    return {
        "suggestions": suggestions
    }


def mock_webinar_details_response() -> Dict[str, Any]:
    """Create mock webinar details API response."""
    return {
        "id": "test-webinar-1",
        "title": "Test Webinar 1",
        "description": "Test description 1",
        "category_name": "Test Category",
        "speakers": ["Test Speaker"],
        "tags": ["test", "webinar"],
        "duration_ms": 1800000,
        "recorded_date": "2024-01-01",
        "video_url": "https://example.com/video1.mp4",
        "pdf_url": "https://example.com/slides1.pdf",
        "status": "published"
    }


def mock_webinars_list_response() -> Dict[str, Any]:
    """Create mock webinars list API response."""
    return {
        "webinars": [
            {
                "id": "test-webinar-1",
                "title": "Test Webinar 1",
                "description": "Test description 1",
                "category_name": "Test Category",
                "speakers": ["Test Speaker"],
                "tags": ["test", "webinar"],
                "duration_ms": 1800000,
                "recorded_date": "2024-01-01",
                "video_url": "https://example.com/video1.mp4",
                "pdf_url": "https://example.com/slides1.pdf"
            }
        ],
        "total": 1,
        "offset": 0,
        "limit": 20,
        "hasMore": False
    }


def mock_categories_response() -> Dict[str, Any]:
    """Create mock categories API response."""
    return {
        "categories": [
            {
                "slug": "test-category",
                "name": "Test Category",
                "count": 5
            }
        ]
    }


def mock_speakers_response() -> Dict[str, Any]:
    """Create mock speakers API response."""
    return {
        "speakers": [
            {
                "name": "Test Speaker",
                "bio": "Test speaker bio",
                "count": 3
            }
        ]
    }


def mock_tags_response() -> Dict[str, Any]:
    """Create mock tags API response."""
    return {
        "tags": [
            {
                "slug": "test-tag",
                "name": "test-tag",
                "count": 10
            }
        ]
    }


def mock_popular_tags_response() -> Dict[str, Any]:
    """Create mock popular tags API response."""
    return {
        "tags": [
            {
                "slug": "popular-tag",
                "name": "popular-tag",
                "count": 20
            }
        ]
    }


def mock_health_response() -> Dict[str, Any]:
    """Create mock health check API response."""
    return {
        "status": "ok"
    }


def mock_health_deep_response() -> Dict[str, Any]:
    """Create mock deep health check API response."""
    return {
        "status": "ok",
        "db": {
            "ok": True,
            "error": None
        },
        "model": {
            "ok": True,
            "name": "paraphrase-multilingual-MiniLM-L12-v2",
            "dims": 384,
            "error": None
        },
        "config": {
            "semanticThreshold": 0.3,
            "fuzzyThreshold": 0.2
        }
    }


def mock_error_response(error_message: str = "Test error") -> Dict[str, Any]:
    """Create mock error API response."""
    return {
        "detail": error_message
    }


def mock_not_found_response() -> Dict[str, Any]:
    """Create mock 404 API response."""
    return {
        "detail": "Webinar not found"
    }


def mock_validation_error_response() -> Dict[str, Any]:
    """Create mock validation error API response."""
    return {
        "detail": [
            {
                "type": "string_too_short",
                "loc": ["query", "q"],
                "msg": "String should have at least 1 character",
                "input": ""
            }
        ]
    }
