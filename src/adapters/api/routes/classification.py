"""Classification debug endpoint — gated by APP_DEBUG."""

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.adapters.api.dependencies import get_classifier, get_app_settings
from src.application.ports.classifier import ClassifierPort
from src.infrastructure.config.settings import Settings
from src.interfaces.schemas.classification import (
    ClassificationResultSchema,
    ClassifyRequest,
    ClassifyResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse)
async def classify_query(
    body: ClassifyRequest,
    classifier: ClassifierPort = Depends(get_classifier),
    settings: Settings = Depends(get_app_settings),
) -> ClassifyResponse:
    if not settings.app_debug:
        raise HTTPException(status_code=404, detail="Not found")

    result = await classifier.classify(body.query)
    logger.info("classify.debug", query=body.query, route=result.route.value)
    return ClassifyResponse.from_route(
        ClassificationResultSchema(
            route=result.route,
            confidence=result.confidence,
            reasoning=result.reasoning,
        )
    )
