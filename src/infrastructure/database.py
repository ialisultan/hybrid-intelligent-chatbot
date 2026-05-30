"""Async SQLAlchemy engine and session management."""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from src.infrastructure.config import Settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for ORM models."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_sqlite_parent_dir(settings: Settings) -> None:
    if not settings.is_sqlite:
        return
    db_path = Path(settings.sqlite_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


def create_engine(settings: Settings) -> AsyncEngine:
    """Create (or return cached) async engine."""
    global _engine, _session_factory
    if _engine is None:
        _ensure_sqlite_parent_dir(settings)
        engine_kwargs: dict = {"echo": settings.app_debug}
        if settings.is_sqlite:
            engine_kwargs["poolclass"] = NullPool
            engine_kwargs["connect_args"] = {"timeout": 30}
        else:
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20
        _engine = create_async_engine(settings.async_database_url, **engine_kwargs)
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database engine not initialised — call create_engine first")
    return _session_factory


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine not initialised — call create_engine first")
    return _engine


async def check_postgres_connection() -> bool:
    """Return True if Postgres accepts a simple SELECT 1."""
    from sqlalchemy import text

    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yield an async DB session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Dispose engine on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
