"""
Test fixtures and sample data for HR Search tests.
"""
import uuid
from typing import Dict, List, Any


def create_test_webinar_data(webinar_id: str = None, **overrides) -> Dict[str, Any]:
    """Create test webinar data with optional overrides."""
    data = {
        "id": webinar_id or str(uuid.uuid4()),
        "title": "Test Webinar Title",
        "description": "Test webinar description for testing purposes",
        "category_id": str(uuid.uuid4()),
        "duration_ms": 1800000,  # 30 minutes
        "video_url": "https://example.com/video.mp4",
        "pdf_url": "https://example.com/slides.pdf",
        "recorded_date": "2024-01-01",
        "status": "published",
        "created_at": "2024-01-01T00:00:00Z"
    }
    data.update(overrides)
    return data


def create_test_speaker_data(speaker_id: str = None, **overrides) -> Dict[str, Any]:
    """Create test speaker data with optional overrides."""
    data = {
        "id": speaker_id or str(uuid.uuid4()),
        "name": "Test Speaker",
        "bio": "Test speaker bio for testing purposes"
    }
    data.update(overrides)
    return data


def create_test_category_data(category_id: str = None, **overrides) -> Dict[str, Any]:
    """Create test category data with optional overrides."""
    data = {
        "id": category_id or str(uuid.uuid4()),
        "name": "Test Category",
        "slug": "test-category"
    }
    data.update(overrides)
    return data


def create_test_tag_data(tag_id: str = None, **overrides) -> Dict[str, Any]:
    """Create test tag data with optional overrides."""
    data = {
        "id": tag_id or str(uuid.uuid4()),
        "name": "test-tag",
        "slug": "test-tag"
    }
    data.update(overrides)
    return data


def create_test_embedding_data(webinar_id: str = None, **overrides) -> Dict[str, Any]:
    """Create test embedding data with optional overrides."""
    data = {
        "webinar_id": webinar_id or str(uuid.uuid4()),
        "embedding_type": "title",
        "vector": [0.1] * 384  # 384-dimensional vector
    }
    data.update(overrides)
    return data


def create_test_search_result(**overrides) -> Dict[str, Any]:
    """Create test search result data with optional overrides."""
    data = {
        "id": str(uuid.uuid4()),
        "title": "Test Search Result",
        "description": "Test search result description",
        "category_name": "Test Category",
        "speakers": ["Test Speaker"],
        "tags": ["test", "search"],
        "duration_ms": 1800000,
        "recorded_date": "2024-01-01",
        "video_url": "https://example.com/video.mp4",
        "pdf_url": "https://example.com/slides.pdf",
        "similarity": 0.85
    }
    data.update(overrides)
    return data


def create_test_autocomplete_suggestion(**overrides) -> Dict[str, Any]:
    """Create test autocomplete suggestion data with optional overrides."""
    data = {
        "suggestion": "Test Suggestion",
        "type": "webinar"
    }
    data.update(overrides)
    return data


def create_multiple_test_webinars(count: int = 5) -> List[Dict[str, Any]]:
    """Create multiple test webinars for bulk testing."""
    webinars = []
    for i in range(count):
        webinar = create_test_webinar_data(
            title=f"Test Webinar {i+1}",
            description=f"Test description for webinar {i+1}"
        )
        webinars.append(webinar)
    return webinars


def create_multiple_test_speakers(count: int = 3) -> List[Dict[str, Any]]:
    """Create multiple test speakers for bulk testing."""
    speakers = []
    for i in range(count):
        speaker = create_test_speaker_data(
            name=f"Test Speaker {i+1}",
            bio=f"Test bio for speaker {i+1}"
        )
        speakers.append(speaker)
    return speakers


def create_multiple_test_tags(count: int = 5) -> List[Dict[str, Any]]:
    """Create multiple test tags for bulk testing."""
    tags = []
    for i in range(count):
        tag = create_test_tag_data(
            name=f"test-tag-{i+1}",
            slug=f"test-tag-{i+1}"
        )
        tags.append(tag)
    return tags


# Sample Polish HR content for realistic testing
POLISH_HR_WEBINARS = [
    {
        "title": "Skuteczna rekrutacja w IT - praktyczny przewodnik",
        "description": "Kompleksowy przewodnik po rekrutacji specjalistów IT. Webinar obejmuje pełny proces rekrutacyjny - od tworzenia atrakcyjnych job description i strategii sourcingu, przez przeprowadzanie skutecznych rozmów kwalifikacyjnych, po wdrożenie nowego pracownika.",
        "tags": ["rekrutacja", "IT", "rozmowa kwalifikacyjna", "sourcing"]
    },
    {
        "title": "Onboarding nowych pracowników - checklist i best practices",
        "description": "Szczegółowy przewodnik po procesie onboarding nowych pracowników, który znacząco wpływa na retencję i zaangażowanie. Webinar obejmuje planowanie pierwszych dni pracy, przygotowanie niezbędnych dokumentów i systemów.",
        "tags": ["onboarding", "dokumenty", "szkolenia", "integracja"]
    },
    {
        "title": "Motywacja zespołu - techniki i narzędzia",
        "description": "Praktyczne techniki motywowania zespołów w różnych sytuacjach. Webinar zawiera case studies z firm technologicznych, metody budowania zaangażowania i strategie radzenia sobie z wyzwaniami motywacyjnymi.",
        "tags": ["motywacja", "zespół", "zaangażowanie", "leadership"]
    }
]


def create_polish_hr_test_data() -> List[Dict[str, Any]]:
    """Create realistic Polish HR test data."""
    webinars = []
    for i, webinar_data in enumerate(POLISH_HR_WEBINARS):
        webinar = create_test_webinar_data(
            title=webinar_data["title"],
            description=webinar_data["description"]
        )
        webinars.append(webinar)
    return webinars
