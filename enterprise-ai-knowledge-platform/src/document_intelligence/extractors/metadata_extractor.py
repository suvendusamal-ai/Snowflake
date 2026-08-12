"""Metadata extractor using CORTEX COMPLETE for intelligent key-value extraction."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from snowflake.snowpark import Session

from src.shared.exceptions import PlatformError
from src.shared.utils import truncate_text

logger = logging.getLogger(__name__)


@dataclass
class MetadataEntry:
    key: str
    value: str
    confidence: float


# Department-specific extraction schemas
EXTRACTION_SCHEMAS: dict[str, list[str]] = {
    "finance": [
        "fiscal_year", "quarter", "revenue", "budget_amount",
        "cost_center", "account_code", "approval_status",
    ],
    "treasury": [
        "instrument_type", "maturity_date", "notional_amount",
        "counterparty", "currency", "interest_rate",
    ],
    "procurement": [
        "vendor_name", "contract_value", "contract_start_date",
        "contract_end_date", "payment_terms", "category",
    ],
    "risk": [
        "risk_category", "likelihood", "impact_level",
        "mitigation_status", "risk_owner", "assessment_date",
    ],
    "compliance": [
        "regulation", "compliance_status", "review_date",
        "next_review_date", "responsible_officer", "finding_count",
    ],
    "audit": [
        "audit_type", "audit_period", "finding_severity",
        "recommendation_count", "auditee", "audit_opinion",
    ],
    "hr": [
        "policy_type", "effective_date", "employee_category",
        "approval_authority", "review_cycle",
    ],
    "legal": [
        "agreement_type", "parties", "effective_date",
        "expiration_date", "jurisdiction", "governing_law",
    ],
    "operations": [
        "process_name", "sla_target", "frequency",
        "responsible_team", "last_review_date",
    ],
}


class MetadataExtractor:
    """Extracts structured metadata from document content using CORTEX COMPLETE."""

    def __init__(self, session: Session, config: dict[str, Any]):
        self.session = session
        self.config = config.get("document_intelligence", {})
        self.model = self.config.get("classification_model", "claude-3-5-haiku")

    def extract(
        self,
        document_id: str,
        content: str,
        file_name: str,
        department: str,
    ) -> list[MetadataEntry]:
        """Extract metadata key-value pairs from document content.

        Uses department-specific extraction schema to guide the LLM.
        """
        # Get extraction fields for this department
        fields = EXTRACTION_SCHEMAS.get(department, EXTRACTION_SCHEMAS["operations"])

        # Build extraction prompt
        content_preview = truncate_text(content, 3000)
        fields_str = ", ".join(fields)

        prompt = f"""Extract the following metadata fields from this document.
File name: {file_name}
Department: {department}
Fields to extract: {fields_str}

For each field, extract the value if present. If a field is not found, use null.
Return ONLY a JSON object mapping field names to extracted values.

Document content:
{content_preview}

JSON output:"""

        try:
            escaped_prompt = prompt.replace("'", "''")
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{escaped_prompt}'
                ) AS EXTRACTION
            """).collect()

            if not result:
                return []

            raw_response = result[0]["EXTRACTION"]
            entries = self._parse_extraction(raw_response, document_id)

            # Persist metadata entries
            self._store_metadata(document_id, entries)

            return entries

        except Exception as e:
            logger.error(f"Metadata extraction failed for {document_id}: {e}")
            return []

    def _parse_extraction(
        self, raw_response: str, document_id: str
    ) -> list[MetadataEntry]:
        """Parse LLM extraction response into MetadataEntry objects."""
        try:
            response_text = raw_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(response_text)
            entries = []

            for key, value in data.items():
                if value is not None and str(value).strip():
                    entries.append(MetadataEntry(
                        key=key,
                        value=str(value).strip(),
                        confidence=0.8,
                    ))

            return entries

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse extraction response for {document_id}: {e}")
            return []

    def _store_metadata(self, document_id: str, entries: list[MetadataEntry]) -> None:
        """Persist extracted metadata to PROCESSED.DOCUMENT_METADATA."""
        if not entries:
            return

        values_clauses = []
        for entry in entries:
            escaped_value = entry.value.replace("'", "''")[:5000]
            values_clauses.append(
                f"('{document_id}', '{entry.key}', '{escaped_value}', "
                f"'cortex_complete', {entry.confidence})"
            )

        values_sql = ",\n".join(values_clauses)
        self.session.sql(f"""
            INSERT INTO PROCESSED.DOCUMENT_METADATA (
                DOCUMENT_ID, METADATA_KEY, METADATA_VALUE,
                EXTRACTION_METHOD, CONFIDENCE
            ) VALUES {values_sql}
        """).collect()

        logger.info(f"Stored {len(entries)} metadata entries for {document_id}")
