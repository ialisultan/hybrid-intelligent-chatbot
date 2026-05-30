"""PostgreSQL persistence adapter."""

from src.adapters.persistence.models import Customer, Order, Product
from src.adapters.persistence.postgres_adapter import PostgresAdapter
from src.adapters.persistence.postgres_repository import PostgresRepository

__all__ = ["Customer", "Order", "PostgresAdapter", "PostgresRepository", "Product"]
