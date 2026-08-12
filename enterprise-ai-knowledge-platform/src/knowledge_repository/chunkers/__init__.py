"""Chunking submodule - document text splitting strategies."""

from .semantic_chunker import Chunk, ChunkConfig, SemanticChunker

__all__ = ["SemanticChunker", "ChunkConfig", "Chunk"]
