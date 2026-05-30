"""LangChain classifier adapter implementing ClassifierPort."""

import structlog
from langchain_core.runnables import Runnable

from src.application.chains.classifier_chain import RouteSchema, rule_based_classify
from src.application.ports.classifier import ClassifierPort
from src.domain.entities.chat import QueryRoute, RouteType
from src.infrastructure.config import Settings

logger = structlog.get_logger(__name__)


class LangChainClassifierAdapter(ClassifierPort):
    """Hybrid classifier: LangChain structured output + rule-based fallback."""

    def __init__(self, chain: Runnable, settings: Settings) -> None:
        self._chain = chain
        self._threshold = settings.classifier_confidence_threshold

    async def classify(self, query: str) -> QueryRoute:
        try:
            result = await self._chain.ainvoke({"query": query})
            if isinstance(result, RouteSchema):
                route_result = QueryRoute(
                    route=result.route,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                )
            elif isinstance(result, dict):
                route_result = QueryRoute(
                    route=RouteType(result["route"]),
                    confidence=float(result.get("confidence", 0.0)),
                    reasoning=str(result.get("reasoning", "")),
                )
            else:
                route_result = QueryRoute(
                    route=result.route,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                )

            if route_result.confidence < self._threshold:
                fallback = rule_based_classify(query)
                logger.info(
                    "classifier.fallback",
                    llm_route=route_result.route.value,
                    fallback_route=fallback.route.value,
                )
                return fallback

            return route_result
        except Exception as exc:
            logger.warning("classifier.llm_failed", error=str(exc))
            return rule_based_classify(query)
