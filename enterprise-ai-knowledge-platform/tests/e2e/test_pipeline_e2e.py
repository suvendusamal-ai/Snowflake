"""End-to-end pipeline test - exercises the full document lifecycle."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from snowflake.snowpark import Session

pytestmark = pytest.mark.e2e

SAMPLE_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "sample_documents"


@pytest.fixture(scope="module")
def session():
    """Real Snowflake session for E2E testing."""
    from src.shared.session import get_session
    with get_session(warehouse="CORTEX_AI_INGESTION_WH") as sess:
        yield sess


@pytest.fixture
def sample_document(tmp_path) -> Path:
    """Create a temporary test document."""
    content = """E2E TEST DOCUMENT - PROCUREMENT

VENDOR ASSESSMENT REPORT
Vendor: Acme Cloud Services Inc.
Assessment Date: January 15, 2025
Assessment Type: Annual Review

1. SERVICE DELIVERY
Overall rating: 4.2/5.0
- Uptime: 99.97% (above SLA of 99.95%)
- Response time P1: 12 minutes (SLA: 15 minutes)
- Resolution time P1: 3.2 hours (SLA: 4 hours)

2. COMMERCIAL TERMS
- Current contract value: $2.4M annually
- Contract end date: December 31, 2025
- Payment terms: Net 30
- Price increase: 3.1% (within CPI + 2% cap)

3. RISK ASSESSMENT
- Financial stability: Strong (Moody's A2)
- Data handling: SOC 2 Type II certified
- Concentration risk: 15% of our cloud spend (acceptable)

4. RECOMMENDATION
Renew contract for 24 months with negotiated 5% volume discount.

Vendor Name: Acme Cloud Services Inc.
Contract Value: $2,400,000
Contract Start Date: 2024-01-01
Contract End Date: 2025-12-31
Payment Terms: Net 30
Category: Cloud Services
"""
    filepath = tmp_path / "E2E_Vendor_Assessment.txt"
    filepath.write_text(content, encoding="utf-8")
    return filepath


class TestFullPipeline:
    """End-to-end: Upload → Parse → Classify → Chunk → Embed → Search."""

    def test_document_ingestion(self, session: Session, sample_document: Path):
        """Test uploading a document and registering it."""
        from src.document_intelligence.service import DocumentIntelligenceService
        from src.shared.config import load_environment_config, load_platform_config

        with pytest.MonkeyPatch.context() as mp:
            service = DocumentIntelligenceService(session)
            result = service.ingest_document(
                file_path=sample_document,
                department="procurement",
                uploaded_by="e2e_test_user",
            )

            assert result.status == "REGISTERED"
            assert result.document_id.startswith("doc_")
            assert result.file_name == "E2E_Vendor_Assessment.txt"

            # Verify in database
            db_result = session.sql(f"""
                SELECT PROCESSING_STATUS, DEPARTMENT
                FROM RAW.DOCUMENT_REGISTRY
                WHERE DOCUMENT_ID = '{result.document_id}'
            """).collect()

            assert len(db_result) == 1
            assert db_result[0]["PROCESSING_STATUS"] == "PENDING"
            assert db_result[0]["DEPARTMENT"] == "procurement"

            return result.document_id

    def test_document_processing(self, session: Session, sample_document: Path):
        """Test the full processing pipeline on a registered document."""
        from src.document_intelligence.service import DocumentIntelligenceService

        service = DocumentIntelligenceService(session)

        # Ingest
        ingest_result = service.ingest_document(
            file_path=sample_document,
            department="procurement",
            uploaded_by="e2e_test",
        )

        # Process
        process_result = service.process_document(ingest_result.document_id)

        assert process_result["status"] == "COMPLETED"
        assert "parse" in process_result["steps"]
        assert process_result["steps"]["parse"]["status"] == "SUCCESS"

        # Verify parsed content exists
        parsed = session.sql(f"""
            SELECT WORD_COUNT FROM PROCESSED.PARSED_DOCUMENTS
            WHERE DOCUMENT_ID = '{ingest_result.document_id}'
        """).collect()

        assert len(parsed) == 1
        assert parsed[0]["WORD_COUNT"] > 50

    def test_chunking_and_embedding(self, session: Session, sample_document: Path):
        """Test that a processed document gets chunked and embedded."""
        from src.document_intelligence.service import DocumentIntelligenceService
        from src.knowledge_repository import KnowledgeRepositoryService

        # Process document
        doc_service = DocumentIntelligenceService(session)
        ingest_result = doc_service.ingest_document(
            sample_document, "procurement", "e2e_test"
        )
        doc_service.process_document(ingest_result.document_id)

        # Get parsed content
        parsed = session.sql(f"""
            SELECT PARSED_CONTENT FROM PROCESSED.PARSED_DOCUMENTS
            WHERE DOCUMENT_ID = '{ingest_result.document_id}'
        """).collect()

        assert len(parsed) > 0
        content = parsed[0]["PARSED_CONTENT"]

        # Index into knowledge base
        kr_service = KnowledgeRepositoryService(session)
        index_result = kr_service.index_document(
            document_id=ingest_result.document_id,
            content=content,
            department="procurement",
            document_type="report",
            sensitivity_level="internal",
            file_name="E2E_Vendor_Assessment.txt",
        )

        assert index_result["status"] == "INDEXED"
        assert index_result["chunk_count"] > 0

        # Verify chunks in database
        chunks = session.sql(f"""
            SELECT COUNT(*) AS CNT FROM KNOWLEDGE.DOCUMENT_CHUNKS
            WHERE DOCUMENT_ID = '{ingest_result.document_id}'
              AND EMBEDDING IS NOT NULL
        """).collect()

        assert chunks[0]["CNT"] > 0

    def test_search_retrieves_indexed_document(self, session: Session, sample_document: Path):
        """Test that search finds our indexed document."""
        from src.document_intelligence.service import DocumentIntelligenceService
        from src.knowledge_repository import KnowledgeRepositoryService

        # Full pipeline
        doc_service = DocumentIntelligenceService(session)
        ingest_result = doc_service.ingest_document(
            sample_document, "procurement", "e2e_test"
        )
        doc_service.process_document(ingest_result.document_id)

        parsed = session.sql(f"""
            SELECT PARSED_CONTENT FROM PROCESSED.PARSED_DOCUMENTS
            WHERE DOCUMENT_ID = '{ingest_result.document_id}'
        """).collect()

        kr_service = KnowledgeRepositoryService(session)
        kr_service.index_document(
            document_id=ingest_result.document_id,
            content=parsed[0]["PARSED_CONTENT"],
            department="procurement",
            file_name="E2E_Vendor_Assessment.txt",
        )

        # Search for content we know is in the document
        results = kr_service.search(
            query="Acme Cloud Services vendor assessment SLA",
            department_filter="procurement",
            limit=5,
        )

        # Should find at least one result
        assert len(results) > 0
        # Top result should reference our document
        found_our_doc = any(
            r.document_id == ingest_result.document_id for r in results
        )
        assert found_our_doc, "Search did not find the indexed test document"

    def test_cleanup(self, session: Session):
        """Clean up E2E test data."""
        session.sql("""
            DELETE FROM KNOWLEDGE.DOCUMENT_CHUNKS
            WHERE FILE_NAME = 'E2E_Vendor_Assessment.txt'
        """).collect()
        session.sql("""
            DELETE FROM KNOWLEDGE.KNOWLEDGE_CATALOG
            WHERE FILE_NAME = 'E2E_Vendor_Assessment.txt'
        """).collect()
        session.sql("""
            DELETE FROM PROCESSED.PARSED_DOCUMENTS
            WHERE DOCUMENT_ID IN (
                SELECT DOCUMENT_ID FROM RAW.DOCUMENT_REGISTRY
                WHERE UPLOADED_BY IN ('e2e_test_user', 'e2e_test')
            )
        """).collect()
        session.sql("""
            DELETE FROM RAW.DOCUMENT_REGISTRY
            WHERE UPLOADED_BY IN ('e2e_test_user', 'e2e_test')
        """).collect()
