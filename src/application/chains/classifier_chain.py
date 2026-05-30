"""Query classifier chain — LLM structured output with rule-based fallback."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.domain.entities.chat import QueryRoute, RouteType

SQL_KEYWORDS = frozenset(
    {
        "total",
        "revenue",
        "orders",
        "order",
        "customers",
        "customer",
        "top",
        "count",
        "sum",
        "list",
        "spending",
        "amount",
        "sales",
        "average",
        "month",
        "week",
        "days",
        "germany",
        "country",
    }
)

VECTOR_KEYWORDS = frozenset(
    {
        "policy",
        "refund",
        "return",
        "warranty",
        "coverage",
        "explain",
        "how",
        "feature",
        "faq",
        "support",
    }
)


class RouteSchema(BaseModel):
    route: RouteType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


classifier_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Classify the user query into exactly one route:\n"
            "- sql: structured data questions about customers, orders, products, "
            "revenue, counts, aggregations, filters, dates\n"
            "- vector: semantic questions about policies, FAQs, product features, "
            "warranty, support articles\n\n"
            "Respond with route, confidence (0-1), and brief reasoning.",
        ),
        ("human", "{query}"),
    ]
)


def build_classifier_chain(chat_model: ChatOpenAI) -> Runnable:
    """Build LangChain structured-output classifier chain."""
    structured_llm = chat_model.with_structured_output(RouteSchema)
    return classifier_prompt | structured_llm


def rule_based_classify(query: str) -> QueryRoute:
    """Keyword fallback for edge cases and low-confidence LLM results."""
    tokens = set(query.lower().replace("?", "").split())
    sql_hits = len(tokens & SQL_KEYWORDS)
    vector_hits = len(tokens & VECTOR_KEYWORDS)

    if sql_hits > vector_hits:
        return QueryRoute(
            route=RouteType.SQL,
            confidence=0.75,
            reasoning="rule-based: SQL keywords dominant",
        )
    if vector_hits > sql_hits:
        return QueryRoute(
            route=RouteType.VECTOR,
            confidence=0.75,
            reasoning="rule-based: vector keywords dominant",
        )
    return QueryRoute(
        route=RouteType.VECTOR,
        confidence=0.6,
        reasoning="rule-based: default to vector",
    )
