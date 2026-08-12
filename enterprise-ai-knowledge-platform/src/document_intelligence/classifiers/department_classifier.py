"""Document classifier using Snowflake CORTEX COMPLETE with structured output."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from snowflake.snowpark import Session

from src.shared.config import load_prompt_templates
from src.shared.exceptions import ClassificationError

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    document_id: str
    department: str
    document_type: str
    sensitivity: str
    topics: list[str]
    confidence: float


class DepartmentClassifier:
    """Classifies documents by department, type, and sensitivity using CORTEX COMPLETE."""

    VALID_DEPARTMENTS = [
        "finance", "treasury", "procurement", "risk",
        "compliance", "audit", "hr", "legal", "operations",
    ]

    VALID_DOC_TYPES = [
        "policy", "report", "memo", "contract",
        "procedure", "manual", "form", "correspondence",
    ]

    VALID_SENSITIVITY = ["public", "internal", "confidential", "restricted"]

    def __init__(self, session: Session, config: dict[str, Any]):
        self.session = session
        self.config = config.get("document_intelligence", {})
        self.model = self.config.get("classification_model", "claude-3-5-haiku")
        self._load_prompt_template()

    def _load_prompt_template(self) -> None:
        """Load classification prompt from templates config."""
        templates = load_prompt_templates()
        self.prompt_template = templates["templates"]["classification_prompt"]["template"]

    def classify(
        self,
        document_id: str,
        content_preview: str,
        file_name: str,
    ) -> ClassificationResult:
        """Classify a document using CORTEX COMPLETE.

        Args:
            document_id: Document identifier.
            content_preview: First ~2000 chars of parsed content.
            file_name: Original file name (provides context hints).

        Returns:
            ClassificationResult with department, type, sensitivity, topics.
        """
        # Build the prompt
        department_list = ", ".join(self.VALID_DEPARTMENTS)
        prompt = self.prompt_template.format(
            department_list=department_list,
            document_preview=content_preview,
        )

        # Add file name context
        prompt = f"File name: {file_name}\n\n{prompt}"

        try:
            # Call CORTEX COMPLETE via SQL
            escaped_prompt = prompt.replace("'", "''")
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{escaped_prompt}'
                ) AS CLASSIFICATION
            """).collect()

            if not result:
                raise ClassificationError("CORTEX COMPLETE returned no result")

            raw_response = result[0]["CLASSIFICATION"]
            classification = self._parse_response(raw_response, document_id)

            # Persist classification
            self._store_classification(classification)

            return classification

        except ClassificationError:
            raise
        except Exception as e:
            raise ClassificationError(
                f"Classification failed for {document_id}: {e}"
            ) from e

    def _parse_response(self, raw_response: str, document_id: str) -> ClassificationResult:
        """Parse and validate the LLM classification response."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = raw_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(response_text)

            # Validate and normalize
            department = data.get("department", "operations").lower()
            if department not in self.VALID_DEPARTMENTS:
                department = "operations"

            doc_type = data.get("document_type", "report").lower()
            if doc_type not in self.VALID_DOC_TYPES:
                doc_type = "report"

            sensitivity = data.get("sensitivity", "internal").lower()
            if sensitivity not in self.VALID_SENSITIVITY:
                sensitivity = "internal"

            topics = data.get("topics", [])
            if not isinstance(topics, list):
                topics = []
            topics = topics[:5]

            return ClassificationResult(
                document_id=document_id,
                department=department,
                document_type=doc_type,
                sensitivity=sensitivity,
                topics=topics,
                confidence=0.85,
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse classification response: {e}. Using defaults.")
            return ClassificationResult(
                document_id=document_id,
                department="operations",
                document_type="report",
                sensitivity="internal",
                topics=[],
                confidence=0.3,
            )

    def _store_classification(self, result: ClassificationResult) -> None:
        """Persist classification result to PROCESSED.DOCUMENT_CLASSIFICATIONS."""
        topics_array = ", ".join(f"'{t}'" for t in result.topics)

        self.session.sql(f"""
            INSERT INTO PROCESSED.DOCUMENT_CLASSIFICATIONS (
                DOCUMENT_ID, DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL,
                TOPICS, CONFIDENCE_SCORE, CLASSIFICATION_MODEL
            ) VALUES (
                '{result.document_id}',
                '{result.department}',
                '{result.document_type}',
                '{result.sensitivity}',
                ARRAY_CONSTRUCT({topics_array}),
                {result.confidence},
                '{self.model}'
            )
        """).collect()

        logger.info(
            f"Classified {result.document_id}: "
            f"dept={result.department}, type={result.document_type}, "
            f"sensitivity={result.sensitivity}"
        )
