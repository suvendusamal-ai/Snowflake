"""Embedding generation service using Snowflake EMBED_TEXT."""

from __future__ import annotations

import logging
from typing import Any

from snowflake.snowpark import Session

from src.shared.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates vector embeddings using Snowflake's native EMBED_TEXT function.

    Uses snowflake-arctic-embed-l-v2.0 (1024 dimensions) for high-quality
    semantic embeddings optimized for retrieval tasks.
    """

    def __init__(self, session: Session, config: dict[str, Any] | None = None):
        self.session = session
        config = config or {}
        kr_config = config.get("knowledge_repository", {})
        self.model = kr_config.get("embedding_model", "snowflake-arctic-embed-l-v2.0")
        self.dimensions = kr_config.get("embedding_dimensions", 1024)

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text string.

        Args:
            text: Text to embed (will be truncated if too long).

        Returns:
            List of floats representing the embedding vector.
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        # EMBED_TEXT has a token limit; truncate to ~8000 chars (~2000 tokens) for safety
        truncated = text[:8000]
        escaped = truncated.replace("'", "''").replace("\\", "\\\\")

        try:
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                    '{self.model}',
                    '{escaped}'
                ) AS EMBEDDING
            """).collect()

            if not result:
                raise EmbeddingError("EMBED_TEXT returned no result")

            embedding = result[0]["EMBEDDING"]

            # Result is a VECTOR type, convert to list if needed
            if isinstance(embedding, list):
                return embedding
            return list(embedding)

        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {e}") from e

    def embed_chunks_batch(
        self,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> int:
        """Generate embeddings for multiple chunks and store in DOCUMENT_CHUNKS.

        Uses batch SQL INSERT with EMBED_TEXT to minimize round-trips.

        Args:
            document_id: Parent document identifier.
            chunks: List of chunk dicts with keys: index, text, section_header,
                    page_number, token_count, department, document_type, etc.

        Returns:
            Number of chunks successfully embedded and stored.
        """
        if not chunks:
            return 0

        stored_count = 0
        batch_size = 10  # Process in batches to avoid SQL size limits

        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start : batch_start + batch_size]

            for chunk in batch:
                try:
                    self._embed_and_store_chunk(document_id, chunk)
                    stored_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to embed chunk {chunk.get('index')} "
                        f"of document {document_id}: {e}"
                    )

        logger.info(
            f"Embedded {stored_count}/{len(chunks)} chunks for document {document_id}"
        )
        return stored_count

    def _embed_and_store_chunk(self, document_id: str, chunk: dict[str, Any]) -> None:
        """Embed a single chunk and insert into KNOWLEDGE.DOCUMENT_CHUNKS."""
        chunk_text = chunk["text"]
        escaped_text = chunk_text.replace("'", "''").replace("\\", "\\\\")

        # Truncate for embedding input
        embed_input = escaped_text[:8000]

        section_header = chunk.get("section_header", "")
        if section_header:
            section_header = section_header.replace("'", "''")

        page_number = chunk.get("page_number")
        page_clause = str(page_number) if page_number else "NULL"

        department = chunk.get("department", "operations")
        document_type = chunk.get("document_type", "report")
        sensitivity = chunk.get("sensitivity_level", "internal")
        file_name = chunk.get("file_name", "").replace("'", "''")

        self.session.sql(f"""
            INSERT INTO KNOWLEDGE.DOCUMENT_CHUNKS (
                DOCUMENT_ID, CHUNK_INDEX, CHUNK_TEXT, CHUNK_SIZE_CHARS,
                TOKEN_COUNT, SECTION_HEADER, PAGE_NUMBER,
                DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL, FILE_NAME,
                EMBEDDING
            )
            SELECT
                '{document_id}',
                {chunk['index']},
                '{escaped_text}',
                {len(chunk_text)},
                {chunk.get('token_count', len(chunk_text) // 4)},
                {'NULL' if not section_header else f"'{section_header}'"},
                {page_clause},
                '{department}',
                '{document_type}',
                '{sensitivity}',
                '{file_name}',
                SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                    '{self.model}',
                    '{embed_input}'
                )
        """).collect()

    def similarity_search(
        self,
        query: str,
        limit: int = 10,
        department_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Perform vector similarity search against DOCUMENT_CHUNKS.

        Note: For production use, prefer Cortex Search Service over raw
        vector search. This method is for fallback/diagnostic purposes.

        Args:
            query: Natural language query to search for.
            limit: Maximum number of results.
            department_filter: Optional department to restrict search.

        Returns:
            List of matching chunks with similarity scores.
        """
        escaped_query = query.replace("'", "''").replace("\\", "\\\\")

        dept_clause = ""
        if department_filter:
            dept_clause = f"AND DEPARTMENT = '{department_filter}'"

        result = self.session.sql(f"""
            SELECT
                CHUNK_ID,
                DOCUMENT_ID,
                CHUNK_TEXT,
                DEPARTMENT,
                FILE_NAME,
                SECTION_HEADER,
                VECTOR_COSINE_SIMILARITY(
                    EMBEDDING,
                    SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                        '{self.model}',
                        '{escaped_query}'
                    )
                ) AS SIMILARITY_SCORE
            FROM KNOWLEDGE.DOCUMENT_CHUNKS
            WHERE EMBEDDING IS NOT NULL
            {dept_clause}
            ORDER BY SIMILARITY_SCORE DESC
            LIMIT {limit}
        """).collect()

        return [
            {
                "chunk_id": row["CHUNK_ID"],
                "document_id": row["DOCUMENT_ID"],
                "chunk_text": row["CHUNK_TEXT"],
                "department": row["DEPARTMENT"],
                "file_name": row["FILE_NAME"],
                "section_header": row["SECTION_HEADER"],
                "score": float(row["SIMILARITY_SCORE"]),
            }
            for row in result
        ]
