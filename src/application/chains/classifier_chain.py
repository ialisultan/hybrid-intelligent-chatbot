"""Query classifier chain — LLM structured output with rule-based fallback."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.domain.entities.chat import QueryRoute, RouteType
from src.interfaces.schemas.classification import ClassificationResultSchema

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
        "average",
        "max",
        "min",
    }
)

VECTOR_KEYWORDS = frozenset(
    {
        "policy",
        "policies",
        "refund",
        "return",
        "warranty",
        "coverage",
        "explain",
        "how",
        "feature",
        "features",
        "faq",
        "support",
        "help",
        "documentation",
        "guide",
        "issue",
        "issues",
    }
)

# Edge-case phrases: policy/doc intent despite SQL-table words
VECTOR_PHRASES = frozenset(
    {
        "orders policy",
        "order policy",
        "customers refund",
        "customer refund",
        "refund policy",
        "return policy",
        "orders policy",
    }
)

CLASSIFIER_SYSTEM_PROMPT = """You are a strict query router for a hybrid chatbot with two mutually exclusive pipelines:

1. SQL — structured database queries (PostgreSQL tables: customers, orders, products)
   Use SQL when the user wants counts, sums, filters, rankings, revenue, dates, or factual records.

2. VECTOR — semantic document search (policies, FAQs, product descriptions, warranty, support)
   Use VECTOR when the user asks about policies, processes, how things work, or document content.

CRITICAL RULES:
- NEVER mix pipelines. Choose exactly one route.
- If the query mentions table-like words (orders, customers) BUT asks about POLICY, PROCESS, FAQ, or SUPPORT → route VECTOR.
- Numeric aggregations, rankings, filters, date ranges → route SQL.
- Product features, explanations, warranty, refunds (as policy) → route VECTOR.

FEW-SHOT EXAMPLES:
Query: "What is the total revenue this month?" → sql (confidence: 0.95)
Query: "Top 5 customers by spending" → sql (confidence: 0.95)
Query: "Orders placed in the last 7 days" → sql (confidence: 0.93)
Query: "What is your return policy?" → vector (confidence: 0.95)
Query: "How does product X work?" → vector (confidence: 0.92)
Query: "Explain warranty coverage" → vector (confidence: 0.94)
Query: "Tell me about orders policy" → vector (confidence: 0.88)  # edge: policy intent
Query: "Customers refund issues" → vector (confidence: 0.87)  # edge: support/policy intent

Respond with route (sql or vector), confidence (0.0-1.0), and brief reasoning."""

classifier_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CLASSIFIER_SYSTEM_PROMPT),
        ("human", "{query}"),
    ]
)


def build_classifier_chain(chat_model: BaseChatModel) -> Runnable:
    """Build LangChain structured-output classifier chain for any chat model."""
    structured_llm = chat_model.with_structured_output(ClassificationResultSchema)
    return classifier_prompt | structured_llm


def rule_based_classify(query: str) -> QueryRoute:
    """Keyword fallback for edge cases and low-confidence LLM results."""
    normalized = query.lower().replace("?", "").strip()

    for phrase in VECTOR_PHRASES:
        if phrase in normalized:
            return QueryRoute(
                route=RouteType.VECTOR,
                confidence=0.82,
                reasoning="rule-based: policy/support phrase detected",
            )

    tokens = set(normalized.split())
    sql_hits = len(tokens & SQL_KEYWORDS)
    vector_hits = len(tokens & VECTOR_KEYWORDS)

    if vector_hits > 0 and sql_hits > 0:
        return QueryRoute(
            route=RouteType.VECTOR,
            confidence=0.78,
            reasoning="rule-based: mixed keywords — policy/doc intent preferred",
        )

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
