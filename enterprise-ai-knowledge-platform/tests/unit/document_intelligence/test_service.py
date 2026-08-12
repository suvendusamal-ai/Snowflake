"""Unit tests for Document Intelligence Service."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.document_intelligence.classifiers.department_classifier import (
    ClassificationResult,
    DepartmentClassifier,
)
from src.document_intelligence.extractors.metadata_extractor import (
    MetadataEntry,
    MetadataExtractor,
)
from src.document_intelligence.service import DocumentIntelligenceService, IngestionResult
from src.shared.exceptions import DocumentIngestionError


@pytest.fixture
def mock_session():
    """Create a mock Snowpark session."""
    session = MagicMock()
    session.sql.return_value.collect.return_value = []
    session.file = MagicMock()
    return session


@pytest.fixture
def mock_config():
    """Minimal environment config for testing."""
    return {
        "document_intelligence": {
            "max_file_size_mb": 50,
            "parse_timeout_seconds": 300,
            "ocr_enabled": True,
            "classification_model": "claude-3-5-haiku",
            "batch_size": 10,
        }
    }


class TestDocumentIntelligenceService:
    """Tests for the main orchestrator."""

    @patch("src.document_intelligence.service.load_environment_config")
    @patch("src.document_intelligence.service.load_platform_config")
    def test_ingest_rejects_unsupported_file_type(
        self, mock_platform, mock_env, mock_session, mock_config, tmp_path
    ):
        mock_env.return_value = mock_config
        mock_platform.return_value = {
            "supported_file_types": [{"extension": ".pdf"}],
            "departments": [{"id": "finance", "stage": "FINANCE_DOCS", "role": "R"}],
        }

        service = DocumentIntelligenceService(mock_session)
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("content")

        with pytest.raises(DocumentIngestionError, match="Unsupported file type"):
            service.ingest_document(str(unsupported_file), "finance")

    @patch("src.document_intelligence.service.load_environment_config")
    @patch("src.document_intelligence.service.load_platform_config")
    def test_ingest_rejects_invalid_department(
        self, mock_platform, mock_env, mock_session, mock_config, tmp_path
    ):
        mock_env.return_value = mock_config
        mock_platform.return_value = {
            "supported_file_types": [{"extension": ".pdf"}],
            "departments": [{"id": "finance", "stage": "FINANCE_DOCS", "role": "R"}],
        }

        service = DocumentIntelligenceService(mock_session)
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        with pytest.raises(DocumentIngestionError, match="Invalid department"):
            service.ingest_document(str(pdf_file), "nonexistent_dept")

    @patch("src.document_intelligence.service.load_environment_config")
    @patch("src.document_intelligence.service.load_platform_config")
    def test_ingest_rejects_missing_file(
        self, mock_platform, mock_env, mock_session, mock_config
    ):
        mock_env.return_value = mock_config
        mock_platform.return_value = {
            "supported_file_types": [{"extension": ".pdf"}],
            "departments": [{"id": "finance", "stage": "FINANCE_DOCS", "role": "R"}],
        }

        service = DocumentIntelligenceService(mock_session)

        with pytest.raises(DocumentIngestionError, match="File not found"):
            service.ingest_document("/nonexistent/path.pdf", "finance")


class TestDepartmentClassifier:
    """Tests for the classification component."""

    @patch("src.document_intelligence.classifiers.department_classifier.load_prompt_templates")
    def test_parse_valid_json_response(self, mock_templates, mock_session, mock_config):
        mock_templates.return_value = {
            "templates": {
                "classification_prompt": {
                    "template": "Classify: {department_list}\n{document_preview}"
                }
            }
        }

        classifier = DepartmentClassifier(mock_session, mock_config)

        valid_response = json.dumps({
            "department": "finance",
            "document_type": "report",
            "sensitivity": "confidential",
            "topics": ["Q4 revenue", "budget planning"],
        })

        result = classifier._parse_response(valid_response, "doc_123")

        assert result.department == "finance"
        assert result.document_type == "report"
        assert result.sensitivity == "confidential"
        assert len(result.topics) == 2

    @patch("src.document_intelligence.classifiers.department_classifier.load_prompt_templates")
    def test_parse_invalid_department_falls_back(self, mock_templates, mock_session, mock_config):
        mock_templates.return_value = {
            "templates": {
                "classification_prompt": {
                    "template": "Classify: {department_list}\n{document_preview}"
                }
            }
        }

        classifier = DepartmentClassifier(mock_session, mock_config)

        response = json.dumps({
            "department": "invalid_dept",
            "document_type": "report",
            "sensitivity": "internal",
            "topics": [],
        })

        result = classifier._parse_response(response, "doc_456")
        assert result.department == "operations"

    @patch("src.document_intelligence.classifiers.department_classifier.load_prompt_templates")
    def test_parse_malformed_json_returns_defaults(self, mock_templates, mock_session, mock_config):
        mock_templates.return_value = {
            "templates": {
                "classification_prompt": {
                    "template": "Classify: {department_list}\n{document_preview}"
                }
            }
        }

        classifier = DepartmentClassifier(mock_session, mock_config)
        result = classifier._parse_response("not valid json at all", "doc_789")

        assert result.department == "operations"
        assert result.confidence == 0.3


class TestMetadataExtractor:
    """Tests for the metadata extraction component."""

    def test_parse_valid_extraction(self, mock_session, mock_config):
        extractor = MetadataExtractor(mock_session, mock_config)

        response = json.dumps({
            "fiscal_year": "2024",
            "revenue": "$1.2B",
            "budget_amount": None,
            "cost_center": "CC-4500",
        })

        entries = extractor._parse_extraction(response, "doc_100")

        # Should exclude null values
        assert len(entries) == 3
        assert entries[0].key == "fiscal_year"
        assert entries[0].value == "2024"

    def test_parse_extraction_handles_code_block(self, mock_session, mock_config):
        extractor = MetadataExtractor(mock_session, mock_config)

        response = '```json\n{"vendor_name": "Acme Corp"}\n```'
        entries = extractor._parse_extraction(response, "doc_200")

        assert len(entries) == 1
        assert entries[0].key == "vendor_name"
        assert entries[0].value == "Acme Corp"

    def test_parse_extraction_handles_garbage(self, mock_session, mock_config):
        extractor = MetadataExtractor(mock_session, mock_config)
        entries = extractor._parse_extraction("I cannot parse this document.", "doc_300")
        assert entries == []
