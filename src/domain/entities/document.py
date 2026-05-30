"""Document retrieval domain DTOs."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    """A document chunk retrieved from the vector store."""

    content: str
    source: str
    score: float
