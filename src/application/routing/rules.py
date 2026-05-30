"""Pure rule-based query routing — no LangChain or infrastructure imports."""

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
        "max",
        "min",
        "placed",
        "ranking",
        "rankings",
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

VECTOR_PHRASES = frozenset(
    {
        "orders policy",
        "order policy",
        "customers refund",
        "customer refund",
        "customers refund issues",
        "customer refund issues",
        "refund policy",
        "return policy",
        "refund issues",
        "about orders policy",
        "about order policy",
    }
)

SQL_AGGREGATION_CUES = frozenset(
    {
        "total",
        "top",
        "sum",
        "count",
        "average",
        "max",
        "min",
        "revenue",
        "spending",
        "last",
        "days",
        "month",
        "week",
        "ranking",
        "rankings",
        "how many",
    }
)

POLICY_SIGNAL_WORDS = frozenset(
    {
        "policy",
        "policies",
        "refund",
        "return",
        "warranty",
        "faq",
        "support",
        "issues",
        "issue",
        "coverage",
        "help",
    }
)

TABLE_WORDS = frozenset({"orders", "order", "customers", "customer", "products", "product"})


def detect_policy_intent(query: str) -> bool:
    """True when the query is about policy/support despite SQL table vocabulary."""
    normalized = query.lower().replace("?", "").strip()

    for phrase in VECTOR_PHRASES:
        if phrase in normalized:
            return True

    tokens = set(normalized.split())
    has_policy_signal = bool(tokens & POLICY_SIGNAL_WORDS) or any(
        w in normalized for w in ("refund", "return policy", "warranty")
    )
    has_table_word = bool(tokens & TABLE_WORDS)
    has_aggregation = bool(tokens & SQL_AGGREGATION_CUES) or any(
        cue in normalized for cue in ("last ", "top ", "total ", "how many")
    )

    if has_policy_signal and has_table_word and not has_aggregation:
        return True

    if has_policy_signal and any(w in normalized for w in ("issue", "issues", "help", "support")):
        return True

    return False


def rule_based_classify(query: str) -> QueryRoute:
    """Keyword and phrase routing for edge cases and low-confidence LLM results."""
    if detect_policy_intent(query):
        return QueryRoute(
            route=RouteType.VECTOR,
            confidence=0.88,
            reasoning="rule-based: policy/support intent detected",
        )

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
