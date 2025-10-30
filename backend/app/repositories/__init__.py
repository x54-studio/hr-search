"""
Repository module exports.

This module exports all repository classes for dependency injection.
"""

from .webinar import WebinarRepository
from .category import CategoryRepository, SpeakerRepository, TagRepository, AutocompleteRepository
from .embedding import EmbeddingRepository

__all__ = [
    "WebinarRepository",
    "CategoryRepository", 
    "SpeakerRepository",
    "TagRepository",
    "AutocompleteRepository",
    "EmbeddingRepository",
]
