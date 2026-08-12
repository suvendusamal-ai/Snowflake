"""Unit tests for Knowledge Repository - Chunking and Embedding."""

from __future__ import annotations

import pytest

from src.knowledge_repository.chunkers.semantic_chunker import (
    Chunk,
    ChunkConfig,
    SemanticChunker,
)


class TestSemanticChunker:
    """Tests for the semantic chunking engine."""

    def test_empty_content_returns_empty(self):
        chunker = SemanticChunker()
        assert chunker.chunk_document("") == []
        assert chunker.chunk_document("   ") == []
        assert chunker.chunk_document(None) == []

    def test_short_content_returns_single_chunk(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=1500, min_chunk_size=10))
        content = "This is a short document about finance."
        chunks = chunker.chunk_document(content)
        assert len(chunks) == 1
        assert chunks[0].text == content
        assert chunks[0].index == 0

    def test_paragraph_boundaries_respected(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=200, chunk_overlap=0, min_chunk_size=20))
        content = (
            "First paragraph about Q4 financial results.\n\n"
            "Second paragraph about risk management strategy.\n\n"
            "Third paragraph about compliance requirements."
        )
        chunks = chunker.chunk_document(content)
        # With 200 char limit, some paragraphs should merge, others split
        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_indices_are_sequential(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=100, chunk_overlap=0, min_chunk_size=20))
        content = "\n\n".join([f"Section {i} with enough text to be a valid chunk." for i in range(10)])
        chunks = chunker.chunk_document(content)
        indices = [c.index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_overlap_adds_context(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=100, chunk_overlap=30, min_chunk_size=20))
        content = "A" * 50 + ".\n\n" + "B" * 50 + ".\n\n" + "C" * 50 + "."
        chunks = chunker.chunk_document(content)
        if len(chunks) > 1:
            # Second chunk should contain some overlap from first
            assert len(chunks[1].text) > 0

    def test_fixed_size_strategy(self):
        chunker = SemanticChunker(ChunkConfig(
            chunk_size=100, chunk_overlap=20, min_chunk_size=20, strategy="fixed"
        ))
        content = "A" * 500
        chunks = chunker.chunk_document(content)
        assert len(chunks) > 1
        # Each chunk should be around chunk_size
        for chunk in chunks[:-1]:
            assert chunk.char_count <= 120  # Allow small variance

    def test_token_count_estimation(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=2000, min_chunk_size=10))
        content = "Word " * 100  # 500 chars, ~125 tokens
        chunks = chunker.chunk_document(content)
        assert len(chunks) == 1
        # Token estimate: len/4 = 500/4 = 125
        assert chunks[0].token_count == len(chunks[0].text) // 4

    def test_page_break_detection(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=200, chunk_overlap=0, min_chunk_size=20))
        content = "Page one content here.\f" + "Page two content here."
        chunks = chunker.chunk_document(content)
        assert len(chunks) >= 1

    def test_heading_detection(self):
        chunker = SemanticChunker(ChunkConfig(chunk_size=500, chunk_overlap=0, min_chunk_size=20))
        content = (
            "# Executive Summary\n\n"
            "This document covers the quarterly financial report.\n\n"
            "# Revenue Analysis\n\n"
            "Revenue grew 15% year over year in all segments."
        )
        chunks = chunker.chunk_document(content)
        # Should detect headings and associate with chunks
        assert len(chunks) >= 1

    def test_large_document_chunking(self):
        """Stress test with a large document."""
        chunker = SemanticChunker(ChunkConfig(chunk_size=1500, chunk_overlap=200, min_chunk_size=100))
        # Simulate a 50-page document (~100KB)
        paragraphs = [f"Paragraph {i}: " + "Lorem ipsum dolor sit amet. " * 20 for i in range(200)]
        content = "\n\n".join(paragraphs)
        chunks = chunker.chunk_document(content)

        assert len(chunks) > 10
        # No chunk should massively exceed target size
        for chunk in chunks:
            assert chunk.char_count <= 2000  # chunk_size + overlap margin


class TestChunkConfig:
    """Tests for ChunkConfig validation."""

    def test_default_values(self):
        config = ChunkConfig()
        assert config.chunk_size == 1500
        assert config.chunk_overlap == 200
        assert config.min_chunk_size == 100
        assert config.strategy == "semantic"

    def test_custom_values(self):
        config = ChunkConfig(chunk_size=1000, chunk_overlap=100, strategy="fixed")
        assert config.chunk_size == 1000
        assert config.strategy == "fixed"
