"""Chat endpoint — accepts user queries and returns routed responses."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request

from src.adapters.api.dependencies import get_chat_use_case
from src.adapters.api.rate_limit import limiter, rate_limit_string
from src.application.usecases.chat import ChatUseCase
from src.infrastructure.config import get_settings
from src.interfaces.schemas.chat import ChatRequest, ChatResponseSchema

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponseSchema)
@limiter.limit(lambda: rate_limit_string(get_settings()))
async def chat(
    request: Request,
    body: ChatRequest,
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> ChatResponseSchema:
    conversation_id: UUID | None = body.conversation_id
    result = await use_case.execute(query=body.query, conversation_id=conversation_id)
    return ChatResponseSchema(
        answer=result.answer,
        route=result.route,
        confidence=result.confidence,
        sources=result.sources,
        sql_query=result.sql_query,
        conversation_id=result.conversation_id,
    )
