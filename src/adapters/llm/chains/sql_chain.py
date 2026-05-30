"""SQL generation chain — NL to SQL via LangChain structured output."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field


class SQLSchema(BaseModel):
    sql: str = Field(description="Read-only SELECT query")
    explanation: str = ""


SQL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Generate a read-only {dialect} SELECT query for the user question.\n"
            "Schema:\n{schema}\n\n"
            "Only output SELECT statements. Never use INSERT, UPDATE, DELETE, or DROP.",
        ),
        ("human", "{query}"),
    ]
)


def build_sql_chain(chat_model: BaseChatModel, dialect: str = "PostgreSQL") -> Runnable:
    """Build LangChain structured-output SQL generation chain."""
    structured_llm = chat_model.with_structured_output(SQLSchema)
    return SQL_PROMPT.partial(dialect=dialect) | structured_llm
