"""Backward-compatible re-export — prefer LangChainSQLPipelineAdapter."""

from src.adapters.persistence.sql_pipeline_adapter import LangChainSQLPipelineAdapter as SQLPipeline

__all__ = ["SQLPipeline"]
