"""Domain-level exceptions — raised by use cases, handled at the API boundary."""


class ChatbotError(Exception):
    """Base exception for all chatbot domain errors."""

    def __init__(self, message: str, *, code: str = "CHATBOT_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ClassificationError(ChatbotError):
    """Query could not be classified into SQL or VECTOR route."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CLASSIFICATION_ERROR")


class RoutingViolationError(ChatbotError):
    """Pipeline attempted to mix SQL and vector retrieval — strictly forbidden."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="ROUTING_VIOLATION")


class PipelineError(ChatbotError):
    """A pipeline (SQL or Vector) failed during execution."""

    def __init__(self, message: str, *, pipeline: str) -> None:
        self.pipeline = pipeline
        super().__init__(message, code=f"{pipeline.upper()}_PIPELINE_ERROR")


class DatabaseError(ChatbotError):
    """PostgreSQL adapter failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="DATABASE_ERROR")


class VectorStoreError(ChatbotError):
    """Vector store adapter failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="VECTOR_STORE_ERROR")
