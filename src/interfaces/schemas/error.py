"""API error response schemas."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by exception handlers."""

    error: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    request_id: str = Field(description="Request correlation ID for support")
