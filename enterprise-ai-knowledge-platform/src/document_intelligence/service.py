"""Document Intelligence Service - orchestrates ingestion, parsing, classification, extraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from snowflake.snowpark import Session

from src.shared.config import load_environment_config, load_platform_config
from src.shared.exceptions import DocumentIngestionError, DocumentParsingError
from src.shared.models import Department, DocumentMetadata, FileType
from src.shared.utils import compute_checksum, generate_id, utc_now

from .classifiers.department_classifier import DepartmentClassifier
from .extractors.metadata_extractor import MetadataExtractor
from .parsers.document_parser import DocumentParser

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    document_id: str
    file_name: str
    stage_path: str
    status: str
    error: str | None = None


class DocumentIntelligenceService:
    """Main orchestrator for document ingestion and processing pipeline."""

    def __init__(self, session: Session):
        self.session = session
        self.config = load_environment_config()
        self.platform_config = load_platform_config()
        self.parser = DocumentParser(session, self.config)
        self.classifier = DepartmentClassifier(session, self.config)
        self.extractor = MetadataExtractor(session, self.config)

    def ingest_document(
        self,
        file_path: str | Path,
        department: str,
        uploaded_by: str | None = None,
    ) -> IngestionResult:
        """Upload a document to the department stage and register it.

        Args:
            file_path: Local path to the file to upload.
            department: Target department identifier.
            uploaded_by: Username of the uploader.

        Returns:
            IngestionResult with document_id and upload status.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise DocumentIngestionError(f"File not found: {file_path}")

        # Validate file type
        extension = file_path.suffix.lower()
        supported = {ft["extension"] for ft in self.platform_config["supported_file_types"]}
        if extension not in supported:
            raise DocumentIngestionError(
                f"Unsupported file type: {extension}. Supported: {supported}"
            )

        # Validate department
        valid_departments = {d["id"] for d in self.platform_config["departments"]}
        if department not in valid_departments:
            raise DocumentIngestionError(
                f"Invalid department: {department}. Valid: {valid_departments}"
            )

        # Get stage name for department
        dept_config = next(d for d in self.platform_config["departments"] if d["id"] == department)
        stage_name = dept_config["stage"]
        document_id = generate_id("doc")

        # Compute checksum
        content = file_path.read_bytes()
        checksum = compute_checksum(content)

        # Upload to stage
        stage_path = f"@RAW.{stage_name}/{document_id}/{file_path.name}"
        try:
            self.session.file.put(
                str(file_path),
                f"@RAW.{stage_name}/{document_id}/",
                auto_compress=False,
                overwrite=True,
            )
            logger.info(f"Uploaded {file_path.name} to {stage_path}")
        except Exception as e:
            raise DocumentIngestionError(f"Stage upload failed: {e}") from e

        # Register in DOCUMENT_REGISTRY
        self.session.sql(f"""
            INSERT INTO RAW.DOCUMENT_REGISTRY (
                DOCUMENT_ID, FILE_NAME, FILE_TYPE, FILE_SIZE_BYTES,
                DEPARTMENT, STAGE_PATH, CHECKSUM_SHA256,
                UPLOADED_BY, PROCESSING_STATUS
            ) VALUES (
                '{document_id}', '{file_path.name}', '{extension}',
                {file_path.stat().st_size}, '{department}', '{stage_path}',
                '{checksum}', '{uploaded_by or "SYSTEM"}', 'PENDING'
            )
        """).collect()

        logger.info(f"Registered document {document_id} in DOCUMENT_REGISTRY")

        return IngestionResult(
            document_id=document_id,
            file_name=file_path.name,
            stage_path=stage_path,
            status="REGISTERED",
        )

    def process_document(self, document_id: str) -> dict[str, Any]:
        """Run the full processing pipeline for a registered document.

        Steps: Parse -> Classify -> Extract Metadata -> Update status.
        """
        # Fetch document record
        doc_row = self.session.sql(f"""
            SELECT DOCUMENT_ID, FILE_NAME, FILE_TYPE, DEPARTMENT, STAGE_PATH
            FROM RAW.DOCUMENT_REGISTRY
            WHERE DOCUMENT_ID = '{document_id}'
        """).collect()

        if not doc_row:
            raise DocumentParsingError(f"Document not found: {document_id}")

        doc = doc_row[0]
        results: dict[str, Any] = {"document_id": document_id, "steps": {}}

        try:
            # Step 1: Parse
            self._update_status(document_id, "PARSING")
            parse_result = self.parser.parse(
                stage_path=doc["STAGE_PATH"],
                file_type=doc["FILE_TYPE"],
                document_id=document_id,
            )
            results["steps"]["parse"] = {"status": "SUCCESS", "word_count": parse_result.word_count}

            # Step 2: Classify
            self._update_status(document_id, "CLASSIFYING")
            classification = self.classifier.classify(
                document_id=document_id,
                content_preview=parse_result.content[:2000],
                file_name=doc["FILE_NAME"],
            )
            results["steps"]["classify"] = {
                "status": "SUCCESS",
                "department": classification.department,
                "doc_type": classification.document_type,
            }

            # Step 3: Extract metadata
            self._update_status(document_id, "EXTRACTING")
            metadata_entries = self.extractor.extract(
                document_id=document_id,
                content=parse_result.content,
                file_name=doc["FILE_NAME"],
                department=classification.department,
            )
            results["steps"]["extract"] = {
                "status": "SUCCESS",
                "metadata_count": len(metadata_entries),
            }

            # Mark complete
            self._update_status(document_id, "COMPLETED")
            results["status"] = "COMPLETED"

        except Exception as e:
            logger.error(f"Processing failed for {document_id}: {e}")
            self._update_status(document_id, "FAILED", error_message=str(e))
            results["status"] = "FAILED"
            results["error"] = str(e)

        return results

    def _update_status(
        self, document_id: str, status: str, error_message: str | None = None
    ) -> None:
        """Update processing status in DOCUMENT_REGISTRY."""
        error_clause = ""
        if error_message:
            escaped = error_message.replace("'", "''")[:5000]
            error_clause = f", ERROR_MESSAGE = '{escaped}'"

        self.session.sql(f"""
            UPDATE RAW.DOCUMENT_REGISTRY
            SET PROCESSING_STATUS = '{status}',
                LAST_PROCESSED_AT = CURRENT_TIMESTAMP()
                {error_clause}
            WHERE DOCUMENT_ID = '{document_id}'
        """).collect()

    def batch_ingest(
        self,
        file_paths: list[str | Path],
        department: str,
        uploaded_by: str | None = None,
    ) -> list[IngestionResult]:
        """Ingest multiple documents in batch."""
        results = []
        for fp in file_paths:
            try:
                result = self.ingest_document(fp, department, uploaded_by)
                results.append(result)
            except DocumentIngestionError as e:
                results.append(IngestionResult(
                    document_id="",
                    file_name=str(fp),
                    stage_path="",
                    status="FAILED",
                    error=str(e),
                ))
        return results
