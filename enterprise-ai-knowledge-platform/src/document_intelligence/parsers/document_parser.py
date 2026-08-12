"""Document parser using Snowflake AI_PARSE_DOCUMENT."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from snowflake.snowpark import Session

from src.shared.exceptions import DocumentParsingError

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    document_id: str
    content: str
    page_count: int | None
    word_count: int
    parse_duration_ms: int
    model: str


class DocumentParser:
    """Parses documents using Snowflake's native AI_PARSE_DOCUMENT function."""

    # File types that support AI_PARSE_DOCUMENT directly
    AI_PARSE_SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".png", ".jpg"}
    TEXT_DIRECT = {".txt", ".csv", ".json"}

    def __init__(self, session: Session, config: dict[str, Any]):
        self.session = session
        self.config = config.get("document_intelligence", {})
        self.timeout = self.config.get("parse_timeout_seconds", 300)
        self.ocr_enabled = self.config.get("ocr_enabled", True)

    def parse(self, stage_path: str, file_type: str, document_id: str) -> ParseResult:
        """Parse a document from a stage path.

        Uses AI_PARSE_DOCUMENT for supported types, direct read for text files.
        """
        start_time = time.time()

        if file_type in self.AI_PARSE_SUPPORTED:
            content, page_count = self._parse_with_ai(stage_path, file_type)
            model = "ai_parse_document"
        elif file_type in self.TEXT_DIRECT:
            content = self._read_text_file(stage_path)
            page_count = None
            model = "direct_read"
        else:
            raise DocumentParsingError(f"No parser available for file type: {file_type}")

        duration_ms = int((time.time() - start_time) * 1000)
        word_count = len(content.split())

        # Persist parsed content
        self._store_parsed_content(
            document_id=document_id,
            content=content,
            page_count=page_count,
            word_count=word_count,
            model=model,
            duration_ms=duration_ms,
        )

        return ParseResult(
            document_id=document_id,
            content=content,
            page_count=page_count,
            word_count=word_count,
            parse_duration_ms=duration_ms,
            model=model,
        )

    def _parse_with_ai(self, stage_path: str, file_type: str) -> tuple[str, int | None]:
        """Parse using AI_PARSE_DOCUMENT with optional OCR."""
        # Determine mode based on file type
        if file_type in {".png", ".jpg"} and self.ocr_enabled:
            mode = "OCR"
        else:
            mode = "LAYOUT"

        try:
            result = self.session.sql(f"""
                SELECT
                    AI_PARSE_DOCUMENT(
                        BUILD_SCOPED_FILE_URL('{stage_path}'),
                        '{mode}'
                    ) AS PARSED
            """).collect()

            if not result:
                raise DocumentParsingError(f"AI_PARSE_DOCUMENT returned no results for {stage_path}")

            parsed_output = result[0]["PARSED"]

            # AI_PARSE_DOCUMENT returns a JSON object with content and metadata
            if isinstance(parsed_output, dict):
                content = parsed_output.get("content", "")
                page_count = parsed_output.get("page_count")
            elif isinstance(parsed_output, str):
                content = parsed_output
                page_count = None
            else:
                content = str(parsed_output)
                page_count = None

            return content, page_count

        except DocumentParsingError:
            raise
        except Exception as e:
            raise DocumentParsingError(
                f"AI_PARSE_DOCUMENT failed for {stage_path}: {e}"
            ) from e

    def _read_text_file(self, stage_path: str) -> str:
        """Read a text file directly from stage."""
        try:
            result = self.session.sql(f"""
                SELECT $1 AS CONTENT
                FROM {stage_path}
                (FILE_FORMAT => (TYPE = 'CSV' FIELD_DELIMITER = NONE RECORD_DELIMITER = NONE))
            """).collect()

            if not result:
                return ""
            return result[0]["CONTENT"]

        except Exception as e:
            raise DocumentParsingError(f"Failed to read text file {stage_path}: {e}") from e

    def _store_parsed_content(
        self,
        document_id: str,
        content: str,
        page_count: int | None,
        word_count: int,
        model: str,
        duration_ms: int,
    ) -> None:
        """Store parsed content in PROCESSED.PARSED_DOCUMENTS."""
        escaped_content = content.replace("'", "''")
        page_clause = f"{page_count}" if page_count else "NULL"

        self.session.sql(f"""
            INSERT INTO PROCESSED.PARSED_DOCUMENTS (
                DOCUMENT_ID, PARSED_CONTENT, PAGE_COUNT, WORD_COUNT,
                PARSE_MODEL, PARSE_DURATION_MS
            ) VALUES (
                '{document_id}',
                '{escaped_content}',
                {page_clause},
                {word_count},
                '{model}',
                {duration_ms}
            )
        """).collect()

        logger.info(
            f"Stored parsed content for {document_id}: "
            f"{word_count} words, {duration_ms}ms"
        )
