"""Provider-agnostic LLM query classifier implementing ClassifierPort."""

import structlog

from src.adapters.llm.chains.classifier_chain import build_classifier_chain
from src.application.ports.chat_model import ChatModelPort
from src.application.ports.classifier import ClassifierPort
from src.application.routing.rules import detect_policy_intent, rule_based_classify
from src.domain.entities.chat import QueryRoute, RouteType
from src.infrastructure.config.settings import Settings
from src.interfaces.schemas.classification import ClassificationResultSchema

logger = structlog.get_logger(__name__)


class LLMQueryClassifier(ClassifierPort):
    """Hybrid classifier: policy pre-check → LLM → rule-based post-correction."""

    def __init__(self, chat_model: ChatModelPort, settings: Settings) -> None:
        self._chain = build_classifier_chain(chat_model.langchain_model)
        self._threshold = settings.classifier_confidence_threshold
        self._provider = chat_model.provider.value

    async def classify(self, query: str) -> QueryRoute:
        if detect_policy_intent(query):
            route = QueryRoute(
                route=RouteType.VECTOR,
                confidence=0.88,
                reasoning="policy intent override (pre-LLM)",
            )
            logger.info(
                "classifier.policy_override",
                route=route.route.value,
                provider=self._provider,
            )
            return route

        try:
            result = await self._chain.ainvoke({"query": query})
            route_result = self._to_query_route(result)

            needs_fallback = (
                route_result.confidence < self._threshold
                or (
                    route_result.route == RouteType.SQL
                    and detect_policy_intent(query)
                )
            )
            if needs_fallback:
                fallback = rule_based_classify(query)
                logger.info(
                    "classifier.fallback",
                    llm_route=route_result.route.value,
                    fallback_route=fallback.route.value,
                    confidence=route_result.confidence,
                    provider=self._provider,
                )
                return fallback

            logger.info(
                "classifier.llm",
                route=route_result.route.value,
                confidence=route_result.confidence,
                provider=self._provider,
            )
            return route_result
        except Exception as exc:
            logger.warning("classifier.llm_failed", error=str(exc), provider=self._provider)
            return rule_based_classify(query)

    @staticmethod
    def _to_query_route(result: object) -> QueryRoute:
        if isinstance(result, ClassificationResultSchema):
            return QueryRoute(
                route=result.route,
                confidence=result.confidence,
                reasoning=result.reasoning,
            )
        if isinstance(result, dict):
            return QueryRoute(
                route=RouteType(result["route"]),
                confidence=float(result.get("confidence", 0.0)),
                reasoning=str(result.get("reasoning", "")),
            )
        return QueryRoute(
            route=result.route,
            confidence=result.confidence,
            reasoning=result.reasoning,
        )
