"""Rule-based classifier implementing ClassifierPort (deterministic routing)."""

from src.application.ports.classifier import ClassifierPort
from src.application.routing.rules import rule_based_classify
from src.domain.entities.chat import QueryRoute


class RuleBasedClassifier(ClassifierPort):
    """Assessment-aligned routing via keyword and phrase rules (no LLM)."""

    async def classify(self, query: str, *, config=None) -> QueryRoute:
        return rule_based_classify(query)
