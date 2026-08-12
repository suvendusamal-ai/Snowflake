"""Knowledge Repository Service - orchestrates chunking, embedding, search, catalog."""

from __future__ import annotations

import logging
from typing import Any

from snowflake.snowpark import Session

from src.shared.config import load_environment_config
from src.shared.exceptions import SearchError
from src.shared.models import Department, SearchResult

from .chunkers.semantic_chunker import Chunk, ChunkConfig, SemanticChunker
from .embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeRepositoryService:
    """Main service for the Knowledge Repository module.

    Provides:
    - Document chunking and embedding
    - Cortex Search integration
    - Knowledge catalog management
    - Vector similarity search (fallback)
    """

    def __init__(self, session: Session, config: dict[str, Any] | None = None):
        self.session = session
        self.config = config or load_environment_config()
        kr_config = self.config.get("knowledge_repository", {})

        self.chunker = SemanticChunker(ChunkConfig(
            chunk_size=kr_config.get("chunk_size", 1500),
            chunk_overlap=kr_config.get("chunk_overlap", 200),
            strategy=kr_config.get("chunking_strategy", "semantic"),
        ))
        self.embedder = EmbeddingService(session, self.config)
        self.search_service = kr_config.get(
            "cortex_search_service", "ENTERPRISE_KNOWLEDGE_SEARCH"
        )
        self.max_results = kr_config.get("max_search_results", 10)

    def index_document(
        self,
        document_id: str,
        content: str,
        department: str,
        document_type: str = "report",
        sensitivity_level: str = "internal",
        file_name: str = "",
    ) -> dict[str, Any]:
        """Chunk, embed, and index a document into the knowledge base.

        Args:
            document_id: Unique document identifier.
            content: Full parsed text content.
            department: Document department for access control.
            document_type: Classification type.
            sensitivity_level: Sensitivity classification.
            file_name: Original file name.

        Returns:
            Dict with indexing results (chunk_count, status).
        """
        # Step 1: Chunk
        chunks = self.chunker.chunk_document(content, document_id)

        if not chunks:
            logger.warning(f"No chunks produced for document {document_id}")
            return {"document_id": document_id, "chunk_count": 0, "status": "NO_CONTENT"}

        # Step 2: Prepare chunk metadata
        chunk_dicts = [
            {
                "index": chunk.index,
                "text": chunk.text,
                "token_count": chunk.token_count,
                "section_header": chunk.section_header,
                "page_number": chunk.page_number,
                "department": department,
                "document_type": document_type,
                "sensitivity_level": sensitivity_level,
                "file_name": file_name,
            }
            for chunk in chunks
        ]

        # Step 3: Embed and store
        stored_count = self.embedder.embed_chunks_batch(document_id, chunk_dicts)

        # Step 4: Update catalog
        self._update_catalog(
            document_id=document_id,
            content=content,
            department=department,
            document_type=document_type,
            sensitivity_level=sensitivity_level,
            file_name=file_name,
            chunk_count=stored_count,
            total_tokens=sum(c.token_count for c in chunks),
        )

        return {
            "document_id": document_id,
            "chunk_count": stored_count,
            "total_chunks": len(chunks),
            "status": "INDEXED",
        }

    def search(
        self,
        query: str,
        department_filter: str | None = None,
        sensitivity_filter: str | None = None,
        limit: int | None = None,
    ) -> list[SearchResult]:
        """Search the knowledge base using Cortex Search Service.

        Args:
            query: Natural language search query.
            department_filter: Restrict to specific department.
            sensitivity_filter: Maximum sensitivity level.
            limit: Max results to return.

        Returns:
            List of SearchResult objects with scores and metadata.
        """
        limit = limit or self.max_results

        # Build filter object for Cortex Search
        filter_obj = self._build_search_filter(department_filter, sensitivity_filter)

        try:
            # Call Cortex Search Service via SQL
            filter_clause = ""
            if filter_obj:
                import json
                filter_json = json.dumps(filter_obj).replace("'", "''")
                filter_clause = f", FILTER => '{filter_json}'"

            escaped_query = query.replace("'", "''")

            result = self.session.sql(f"""
                SELECT PARSE_JSON(
                    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                        'KNOWLEDGE.{self.search_service}',
                        '{escaped_query}',
                        {limit}
                        {filter_clause}
                    )
                ) AS RESULTS
            """).collect()

            if not result:
                return []

            # Parse Cortex Search results
            search_results = result[0]["RESULTS"]
            return self._parse_search_results(search_results)

        except Exception as e:
            logger.error(f"Cortex Search failed: {e}")
            # Fallback to vector similarity search
            logger.info("Falling back to vector similarity search")
            return self._fallback_vector_search(query, department_filter, limit)

    def _build_search_filter(
        self,
        department: str | None,
        sensitivity: str | None,
    ) -> dict[str, Any] | None:
        """Build Cortex Search filter object."""
        conditions = []

        if department:
            conditions.append({"@eq": {"DEPARTMENT": department}})
        if sensitivity:
            # Allow access to specified level and below
            allowed = self._sensitivity_levels_at_or_below(sensitivity)
            conditions.append({"@in": {"SENSITIVITY_LEVEL": allowed}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"@and": conditions}

    def _sensitivity_levels_at_or_below(self, level: str) -> list[str]:
        """Return sensitivity levels at or below the given level."""
        hierarchy = ["public", "internal", "confidential", "restricted"]
        try:
            idx = hierarchy.index(level.lower())
            return hierarchy[: idx + 1]
        except ValueError:
            return ["public", "internal"]

    def _parse_search_results(self, raw_results: Any) -> list[SearchResult]:
        """Parse Cortex Search response into SearchResult objects."""
        results = []
        if isinstance(raw_results, dict) and "results" in raw_results:
            items = raw_results["results"]
        elif isinstance(raw_results, list):
            items = raw_results
        else:
            return []

        for item in items:
            try:
                results.append(SearchResult(
                    chunk_id=item.get("CHUNK_ID", ""),
                    document_id=item.get("DOCUMENT_ID", ""),
                    chunk_text=item.get("CHUNK_TEXT", ""),
                    score=float(item.get("score", item.get("SCORE", 0.0))),
                    document_name=item.get("FILE_NAME", ""),
                    department=Department(item.get("DEPARTMENT", "operations")),
                    metadata={
                        "section_header": item.get("SECTION_HEADER"),
                        "document_type": item.get("DOCUMENT_TYPE"),
                        "sensitivity": item.get("SENSITIVITY_LEVEL"),
                    },
                ))
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse search result: {e}")
                continue

        return results

    def _fallback_vector_search(
        self,
        query: str,
        department: str | None,
        limit: int,
    ) -> list[SearchResult]:
        """Fallback: direct vector cosine similarity search."""
        raw_results = self.embedder.similarity_search(
            query=query,
            limit=limit,
            department_filter=department,
        )

        return [
            SearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                chunk_text=r["chunk_text"],
                score=r["score"],
                document_name=r["file_name"],
                department=Department(r["department"]),
                metadata={"section_header": r.get("section_header")},
            )
            for r in raw_results
        ]

    def _update_catalog(
        self,
        document_id: str,
        content: str,
        department: str,
        document_type: str,
        sensitivity_level: str,
        file_name: str,
        chunk_count: int,
        total_tokens: int,
    ) -> None:
        """Insert or update the knowledge catalog entry for a document."""
        summary = content[:2000].replace("'", "''")
        escaped_name = file_name.replace("'", "''")

        self.session.sql(f"""
            MERGE INTO KNOWLEDGE.KNOWLEDGE_CATALOG tgt
            USING (SELECT '{document_id}' AS DOCUMENT_ID) src
            ON tgt.DOCUMENT_ID = src.DOCUMENT_ID
            WHEN MATCHED THEN UPDATE SET
                CHUNK_COUNT = {chunk_count},
                TOTAL_TOKENS = {total_tokens},
                LAST_UPDATED_AT = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT (
                DOCUMENT_ID, TITLE, SUMMARY, DEPARTMENT,
                DOCUMENT_TYPE, SENSITIVITY_LEVEL, CHUNK_COUNT,
                TOTAL_TOKENS, FILE_NAME
            ) VALUES (
                '{document_id}', '{escaped_name}', '{summary}',
                '{department}', '{document_type}', '{sensitivity_level}',
                {chunk_count}, {total_tokens}, '{escaped_name}'
            )
        """).collect()

    def get_catalog(
        self,
        department: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve knowledge catalog entries."""
        dept_clause = f"WHERE DEPARTMENT = '{department}'" if department else ""

        result = self.session.sql(f"""
            SELECT
                CATALOG_ID, DOCUMENT_ID, TITLE, SUMMARY,
                DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL,
                CHUNK_COUNT, TOTAL_TOKENS, FILE_NAME, FILE_TYPE,
                FIRST_INDEXED_AT, LAST_UPDATED_AT
            FROM KNOWLEDGE.KNOWLEDGE_CATALOG
            {dept_clause}
            ORDER BY LAST_UPDATED_AT DESC
            LIMIT {limit}
        """).collect()

        return [dict(row) for row in result]

    def remove_document(self, document_id: str) -> None:
        """Remove a document from the knowledge base (chunks + catalog)."""
        self.session.sql(f"""
            DELETE FROM KNOWLEDGE.DOCUMENT_CHUNKS
            WHERE DOCUMENT_ID = '{document_id}'
        """).collect()

        self.session.sql(f"""
            DELETE FROM KNOWLEDGE.KNOWLEDGE_CATALOG
            WHERE DOCUMENT_ID = '{document_id}'
        """).collect()

        logger.info(f"Removed document {document_id} from knowledge base")
