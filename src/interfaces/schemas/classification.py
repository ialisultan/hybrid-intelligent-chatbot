"""Classification API and LLM structured-output schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from src.domain.entities.chat import RouteType


class ClassificationResultSchema(BaseModel):
    """Query classification result — used by LLM structured output and API."""

    route: RouteType
    confidence: float = Field(ge=0.0, le=1.0, description="Classifier confidence score")
    reasoning: str = Field(default="", description="Brief explanation of routing decision")


class ClassifyRequest(BaseModel):
    """Request body for the classify debug endpoint."""

    query: str = Field(..., min_length=1, max_length=4000)


class ClassifyResponse(ClassificationResultSchema):
    """Response for the classify debug endpoint."""

    route_label: Literal["SQL", "VECTOR"] = Field(
        description="Human-readable route label for assessment demos"
    )

    @classmethod
    def from_route(cls, result: ClassificationResultSchema) -> "ClassifyResponse":
        label = "SQL" if result.route == RouteType.SQL else "VECTOR"
        return cls(route=result.route, confidence=result.confidence, reasoning=result.reasoning, route_label=label)
