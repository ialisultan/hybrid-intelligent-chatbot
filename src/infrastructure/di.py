"""Dependency injection container — wires ports, chains, and LangGraph.

Stub mode (no API keys): StubClassifier + StubSQLPipeline + StubVectorPipeline.
Real mode: LLMQueryClassifier + LangChain pipeline adapters + FAISS/Qdrant.
"""

from dataclasses import dataclass, field

import structlog

from src.adapters.llm.provider_factory import create_providers
from src.adapters.llm.query_classifier import LLMQueryClassifier
from src.adapters.llm.stub import StubClassifier, StubSQLPipeline, StubVectorPipeline
from src.adapters.persistence.postgres_adapter import PostgresAdapter
from src.adapters.persistence.sql_pipeline_adapter import LangChainSQLPipelineAdapter
from src.adapters.repositories.conversation_repository import InMemoryConversationRepository
from src.adapters.vector.factory import create_vector_store
from src.adapters.vector.vector_pipeline_adapter import LangChainVectorPipelineAdapter
from src.application.orchestrator import ChatOrchestrator, create_orchestrator
from src.application.ports.chat_model import ChatModelPort
from src.application.ports.classifier import ClassifierPort
from src.application.ports.embedding import EmbeddingPort
from src.application.ports.repository import ConversationRepositoryPort
from src.application.ports.sql_executor import SQLExecutorPort
from src.application.ports.sql_pipeline import SQLPipelinePort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.application.ports.vector_store import VectorStorePort
from src.application.usecases.chat import ChatUseCase
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config import Settings, get_settings
from src.infrastructure.database import create_engine

logger = structlog.get_logger(__name__)


@dataclass
class Container:
    """Application-wide dependency container."""

    settings: Settings = field(default_factory=get_settings)
    chat_model: ChatModelPort | None = None
    embeddings: EmbeddingPort | None = None
    sql_executor: SQLExecutorPort | None = None
    vector_store: VectorStorePort | None = None
    classifier: ClassifierPort | None = None
    sql_pipeline: SQLPipelinePort | None = None
    vector_pipeline: VectorPipelinePort | None = None
    conversation_repo: ConversationRepositoryPort | None = None
    orchestrator: ChatOrchestrator | None = None
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
        self.sql_executor = PostgresAdapter(self.settings)
        self.conversation_repo = InMemoryConversationRepository()

        chat_model, embeddings = create_providers(self.settings)
        self.chat_model = chat_model
        self.embeddings = embeddings

        logger.info(
            "container.init.providers",
            chat_provider=chat_model.provider.value,
            embedding_provider=embeddings.provider.value,
        )

        if chat_model.provider == LLMProvider.STUB:
            logger.warning("container.init.stub_mode", msg="Using stub pipelines")
            classifier = StubClassifier()
            sql_pipeline: SQLPipelinePort = StubSQLPipeline()
            vector_pipeline: VectorPipelinePort = StubVectorPipeline()
        else:
            self.vector_store = create_vector_store(
                self.settings, embeddings.langchain_embeddings
            )
            classifier = LLMQueryClassifier(chat_model, self.settings)
            vector_pipeline = LangChainVectorPipelineAdapter(
                self.vector_store, chat_model, self.settings
            )
            sql_pipeline = LangChainSQLPipelineAdapter(
                chat_model, self.sql_executor, self.settings
            )

        self.classifier = classifier
        self.sql_pipeline = sql_pipeline
        self.vector_pipeline = vector_pipeline

        orchestrator = create_orchestrator(
            classifier=classifier,
            sql_pipeline=sql_pipeline,
            vector_pipeline=vector_pipeline,
            conversation_repo=self.conversation_repo,
            history_limit=self.settings.conversation_history_limit,
        )
        self.orchestrator = orchestrator
        self.chat_use_case = ChatUseCase(
            orchestrator=orchestrator,
            conversation_repo=self.conversation_repo,
        )

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
