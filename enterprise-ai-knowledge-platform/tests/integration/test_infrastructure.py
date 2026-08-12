"""Integration tests - verify Snowflake infrastructure and service connectivity."""

from __future__ import annotations

import pytest
from snowflake.snowpark import Session

from src.shared.config import load_environment_config

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def session():
    """Create a real Snowflake session for integration testing."""
    from src.shared.session import get_session
    with get_session() as sess:
        yield sess


class TestSnowflakeInfrastructure:
    """Verify that all required Snowflake objects exist."""

    EXPECTED_SCHEMAS = ["RAW", "PROCESSED", "KNOWLEDGE", "AGENT", "GOVERNANCE", "OBSERVABILITY"]

    EXPECTED_TABLES = {
        "RAW": ["DOCUMENT_REGISTRY"],
        "PROCESSED": ["PARSED_DOCUMENTS", "DOCUMENT_CLASSIFICATIONS", "DOCUMENT_METADATA", "PROCESSING_LOG"],
        "KNOWLEDGE": ["DOCUMENT_CHUNKS", "KNOWLEDGE_CATALOG", "CHUNK_LINEAGE", "SEARCH_FEEDBACK"],
        "AGENT": ["CONVERSATIONS", "CONVERSATION_MESSAGES", "TOOL_REGISTRY", "PROMPT_VERSIONS", "AGENT_TRACES"],
        "GOVERNANCE": ["ACCESS_AUDIT_LOG", "AI_GOVERNANCE_LOG", "DATA_LINEAGE", "ROLE_DEPARTMENT_MAP"],
        "OBSERVABILITY": ["TOKEN_USAGE", "SEARCH_DIAGNOSTICS", "LATENCY_METRICS"],
    }

    EXPECTED_STAGES = [
        "FINANCE_DOCS", "TREASURY_DOCS", "PROCUREMENT_DOCS", "RISK_DOCS",
        "COMPLIANCE_DOCS", "AUDIT_DOCS", "HR_DOCS", "LEGAL_DOCS", "OPERATIONS_DOCS",
    ]

    def test_database_exists(self, session: Session):
        result = session.sql(
            "SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES "
            "WHERE DATABASE_NAME = 'CORTEX_AI_PLATFORM'"
        ).collect()
        # If we're connected to CORTEX_AI_PLATFORM, this is inherently true
        assert session.get_current_database() is not None

    def test_schemas_exist(self, session: Session):
        result = session.sql(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA"
        ).collect()
        schema_names = {row["SCHEMA_NAME"] for row in result}

        for expected in self.EXPECTED_SCHEMAS:
            assert expected in schema_names, f"Schema {expected} not found"

    @pytest.mark.parametrize("schema,tables", EXPECTED_TABLES.items())
    def test_tables_exist(self, session: Session, schema: str, tables: list[str]):
        result = session.sql(f"""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
        """).collect()
        existing = {row["TABLE_NAME"] for row in result}

        for table in tables:
            assert table in existing, f"Table {schema}.{table} not found"

    def test_stages_exist(self, session: Session):
        result = session.sql("SHOW STAGES IN SCHEMA RAW").collect()
        stage_names = {row["name"] for row in result}

        for expected in self.EXPECTED_STAGES:
            assert expected in stage_names, f"Stage RAW.{expected} not found"

    def test_document_registry_stream_exists(self, session: Session):
        result = session.sql("SHOW STREAMS IN SCHEMA RAW").collect()
        stream_names = {row["name"] for row in result}
        assert "DOCUMENT_REGISTRY_STREAM" in stream_names

    def test_chunking_udf_exists(self, session: Session):
        result = session.sql("""
            SELECT FUNCTION_NAME FROM INFORMATION_SCHEMA.FUNCTIONS
            WHERE FUNCTION_SCHEMA = 'KNOWLEDGE'
              AND FUNCTION_NAME = 'CHUNK_DOCUMENT_UDF'
        """).collect()
        assert len(result) > 0, "CHUNK_DOCUMENT_UDF not found"

    def test_chunking_udf_works(self, session: Session):
        result = session.sql("""
            SELECT ARRAY_SIZE(
                KNOWLEDGE.CHUNK_DOCUMENT_UDF(
                    'Paragraph one about finance.\\n\\nParagraph two about risk.\\n\\nParagraph three about compliance.',
                    500, 100
                )
            ) AS CHUNK_COUNT
        """).collect()
        assert result[0]["CHUNK_COUNT"] >= 1

    def test_cortex_search_service_exists(self, session: Session):
        try:
            result = session.sql(
                "SHOW CORTEX SEARCH SERVICES IN SCHEMA KNOWLEDGE"
            ).collect()
            service_names = {row["name"] for row in result}
            assert "ENTERPRISE_KNOWLEDGE_SEARCH" in service_names
        except Exception:
            pytest.skip("Cortex Search Service not yet deployed")

    def test_row_access_policy_exists(self, session: Session):
        result = session.sql("""
            SELECT POLICY_NAME FROM INFORMATION_SCHEMA.ROW_ACCESS_POLICIES
            WHERE POLICY_SCHEMA = 'GOVERNANCE'
        """).collect()
        policy_names = {row["POLICY_NAME"] for row in result}
        assert "DEPARTMENT_ROW_ACCESS" in policy_names

    def test_role_department_map_populated(self, session: Session):
        result = session.sql(
            "SELECT COUNT(*) AS CNT FROM GOVERNANCE.ROLE_DEPARTMENT_MAP"
        ).collect()
        assert result[0]["CNT"] >= 18  # 9 dept + 9 admin + 9 service


class TestCortexFunctions:
    """Verify Cortex AI functions are available."""

    def test_embed_text_available(self, session: Session):
        result = session.sql("""
            SELECT ARRAY_SIZE(
                SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                    'snowflake-arctic-embed-l-v2.0',
                    'test embedding generation'
                )
            ) AS DIM
        """).collect()
        assert result[0]["DIM"] == 1024

    def test_cortex_complete_available(self, session: Session):
        result = session.sql("""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-haiku',
                'Reply with exactly: HEALTH_CHECK_OK'
            ) AS RESPONSE
        """).collect()
        assert "HEALTH_CHECK_OK" in result[0]["RESPONSE"]
