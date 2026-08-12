"""Shared test fixtures and configuration."""

import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no Snowflake connection)")
    config.addinivalue_line("markers", "integration: Integration tests (requires Snowflake)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full pipeline)")


@pytest.fixture
def sample_documents_dir() -> Path:
    """Path to generated sample documents."""
    return PROJECT_ROOT / "data" / "sample_documents"


@pytest.fixture
def sample_finance_doc(sample_documents_dir) -> Path:
    """Path to a sample finance document."""
    return sample_documents_dir / "finance" / "Q4_2024_Financial_Report.txt"


@pytest.fixture
def sample_procurement_doc(sample_documents_dir) -> Path:
    """Path to a sample procurement document."""
    return sample_documents_dir / "procurement" / "Vendor_Contract_Template_2024.txt"
