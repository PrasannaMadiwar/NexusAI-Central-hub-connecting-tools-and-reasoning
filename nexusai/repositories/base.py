"""
Base Repository Interface following the Dependency Inversion Principle (DIP).
Decouples domain services from concrete data persistence technologies.
"""
from typing import Generic, TypeVar, Optional, List
from abc import ABC, abstractmethod

T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """Generic interface for data access repositories."""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Retrieve an entity by primary key identifier."""
        pass
