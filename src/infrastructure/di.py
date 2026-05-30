"""Dependency injection container — wires ports, chains, and LangGraph."""

from dataclasses import dataclass, field

import structlog

from src.adapters.llm.chain_factory import build_classifier_runnable, build_rag_chain
from src.adapters.llm.classifier_adapter import LangChainClassifierAdapter
from src.adapters.llm.langchain_llm import LangChainLLMAdapter
from src.adapters.vector.factory import create_vector_store
from src.application.chains.sql_chain import build_sql_chain
from src.application.orchestrator import create_orchestrator
from src.application.services.sql_pipeline import SQLPipeline
from src.application.services.vector_pipeline import VectorPipeline
from src.application.usecases.chat import ChatUseCase
from src.infrastructure.config import Settings, get_settings
from src.infrastructure.database import create_engine

logger = structlog.get_logger(__name__)


@dataclass
class Container:
    """Application-wide dependency container."""

    settings: Settings = field(default_factory=get_settings)
    chat_use_case: ChatUseCase | None = None
    _initialised: bool = False

    async def init(self) -> None:
        """Initialise adapters, LangChain chains, and LangGraph orchestrator."""
        if self._initialised:
            return

        logger.info(
            "container.init.start",
            env=self.settings.app_env,
            vector_backend=self.settings.vector_store_backend,
        )

        create_engine(self.settings)

        if self.settings.openai_api_key:
            llm = LangChainLLMAdapter(self.settings)
            vector_store = create_vector_store(self.settings, llm.embeddings)
            rag_chain = build_rag_chain(vector_store, llm, self.settings)
            classifier_chain = build_classifier_runnable(llm)
            sql_chain = build_sql_chain(llm.chat_model)

            classifier = LangChainClassifierAdapter(classifier_chain, self.settings)
            vector_pipeline = VectorPipeline(rag_chain)
            sql_pipeline = SQLPipeline(sql_chain)
        else:
            logger.warning("container.init.no_openai_key", msg="Using stub pipelines")
            from src.adapters.llm.stub import StubClassifier, StubSQLPipeline, StubVectorPipeline

            classifier = StubClassifier()
            sql_pipeline = StubSQLPipeline()
            vector_pipeline = StubVectorPipeline()

        orchestrator = create_orchestrator(
            classifier=classifier,
            sql_pipeline=sql_pipeline,
            vector_pipeline=vector_pipeline,
        )
        self.chat_use_case = ChatUseCase(orchestrator=orchestrator)

        self._initialised = True
        logger.info("container.init.complete")

    async def shutdown(self) -> None:
        """Release resources on application shutdown."""
        from src.infrastructure.database import dispose_engine

        await dispose_engine()
        self._initialised = False
        logger.info("container.shutdown.complete")


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container
