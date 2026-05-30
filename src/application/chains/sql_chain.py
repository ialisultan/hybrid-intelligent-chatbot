"""SQL generation chain — NL to SQL via LangChain structured output (stub execution)."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class SQLSchema(BaseModel):
    sql: str = Field(description="Read-only SELECT query")
    explanation: str = ""


SQL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Generate a read-only PostgreSQL SELECT query for the user question.\n"
            "Schema:\n"
            "- customers(id, name, email, country)\n"
            "- orders(id, customer_id, product_name, amount, order_date)\n"
            "- products(id, name, category, price)\n\n"
            "Only output SELECT statements. Never use INSERT, UPDATE, DELETE, or DROP.",
        ),
        ("human", "{query}"),
    ]
)


def build_sql_chain(chat_model: ChatOpenAI) -> Runnable:
    """Build LangChain structured-output SQL generation chain."""
    structured_llm = chat_model.with_structured_output(SQLSchema)
    return SQL_PROMPT | structured_llm
