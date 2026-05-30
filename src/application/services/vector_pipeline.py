"""Backward-compatible re-export — prefer LangChainVectorPipelineAdapter."""

from src.adapters.vector.vector_pipeline_adapter import LangChainVectorPipelineAdapter as VectorPipeline

__all__ = ["VectorPipeline"]
