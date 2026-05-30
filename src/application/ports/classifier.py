"""Classifier port — determines SQL vs VECTOR routing."""

from abc import ABC, abstractmethod

from src.domain.entities.chat import QueryRoute


class ClassifierPort(ABC):
    """Classify incoming natural-language queries into strict routes."""

    @abstractmethod
    async def classify(self, query: str) -> QueryRoute:
        """Return route type with confidence score and reasoning."""
        ...
