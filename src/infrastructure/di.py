"""Dependency injection container — wires ports, chains, and LangGraph.

Stub mode (no API keys): RuleBasedClassifier + StubSQLPipeline + StubVectorPipeline.
Real mode: LLMQueryClassifier + LangChain pipeline adapters + FAISS/Qdrant/Pinecone.
"""

from dataclasses import dataclass, field

import structlog

from src.adapters.llm.provider_factory import create_providers
from src.adapters.llm.query_classifier import LLMQueryClassifier
from src.adapters.llm.rule_classifier import RuleBasedClassifier
from src.adapters.llm.stub import StubSQLPipeline, StubVectorPipeline
from src.adapters.persistence.postgres_adapter import PostgresAdapter
from src.adapters.persistence.sql_pipeline_adapter import LangChainSQLPipelineAdapter
from src.adapters.repositories.factory import create_conversation_repository
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

        self._wire_persistence()
        self._wire_providers()

        if self.chat_model and self.chat_model.provider == LLMProvider.STUB:
            logger.warning("container.init.stub_mode", msg="Using stub pipelines")
            self.classifier = self._build_classifier()
            self.sql_pipeline = StubSQLPipeline()
            self.vector_pipeline = StubVectorPipeline()
        else:
            assert self.chat_model is not None
            self.vector_store = create_vector_store(
                self.settings, self.embeddings.langchain_embeddings  # type: ignore[union-attr]
            )
            self.classifier = self._build_classifier()
            self.sql_pipeline = self._build_sql_pipeline()
            self.vector_pipeline = self._build_vector_pipeline()

        self.orchestrator = self._build_orchestrator()
        self.chat_use_case = ChatUseCase(
            orchestrator=self.orchestrator,
            conversation_repo=self.conversation_repo,
        )

        self._initialised = True
        logger.info("container.init.complete")

    def _wire_persistence(self) -> None:
        create_engine(self.settings)
        self.sql_executor = PostgresAdapter(self.settings)
        self.conversation_repo = create_conversation_repository(self.settings)
        logger.info(
            "container.init.conversation_repo",
            backend=self.settings.conversation_repository,
        )

    def _wire_providers(self) -> None:
        chat_model, embeddings = create_providers(self.settings)
        self.chat_model = chat_model
        self.embeddings = embeddings
        logger.info(
            "container.init.providers",
            chat_provider=chat_model.provider.value,
            embedding_provider=embeddings.provider.value,
        )

    def _build_classifier(self) -> ClassifierPort:
        if self.chat_model and self.chat_model.provider == LLMProvider.STUB:
            return RuleBasedClassifier()
        return LLMQueryClassifier(self.chat_model, self.settings)  # type: ignore[arg-type]

    def _build_sql_pipeline(self) -> SQLPipelinePort:
        return LangChainSQLPipelineAdapter(
            self.chat_model,  # type: ignore[arg-type]
            self.sql_executor,  # type: ignore[arg-type]
            self.settings,
        )

    def _build_vector_pipeline(self) -> VectorPipelinePort:
        return LangChainVectorPipelineAdapter(
            self.vector_store,  # type: ignore[arg-type]
            self.chat_model,  # type: ignore[arg-type]
            self.settings,
        )

    def _build_orchestrator(self) -> ChatOrchestrator:
        return create_orchestrator(
            classifier=self.classifier,  # type: ignore[arg-type]
            sql_pipeline=self.sql_pipeline,  # type: ignore[arg-type]
            vector_pipeline=self.vector_pipeline,  # type: ignore[arg-type]
            conversation_repo=self.conversation_repo,
            history_limit=self.settings.conversation_history_limit,
        )

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


def reset_container() -> None:
    """Clear global container and settings cache (for tests)."""
    global _container
    _container = None
    get_settings.cache_clear()
