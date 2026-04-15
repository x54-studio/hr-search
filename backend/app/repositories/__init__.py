"""
Repository module exports.

This module exports all repository classes for dependency injection.
"""

from .item import ItemRepository
from .category import CategoryRepository, SpeakerRepository, TagRepository, AutocompleteRepository
from .embedding import EmbeddingRepository

__all__ = [
    "ItemRepository",
    "CategoryRepository",
    "SpeakerRepository",
    "TagRepository",
    "AutocompleteRepository",
    "EmbeddingRepository",
]
