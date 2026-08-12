"""Governance Audit Logger - records access, AI decisions, and guardrail outcomes."""

from __future__ import annotations

import json
import logging
from typing import Any

from snowflake.snowpark import Session

from src.shared.utils import generate_id

logger = logging.getLogger(__name__)


class AuditLogger:
    """Records governance events to Snowflake audit tables.

    Event categories:
    - ACCESS: Document access, search queries, data retrieval
    - AI_DECISION: Model invocations, tool calls, response generation
    - GUARDRAIL: Validation outcomes, violations, actions taken
    - ADMIN: Configuration changes, role grants, policy modifications
    """

    def __init__(self, session: Session):
        self.session = session

    def log_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        department: str | None = None,
        outcome: str = "SUCCESS",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log a data access event."""
        self._insert_access_log(
            event_type="ACCESS",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            department=department,
            outcome=outcome,
            details=details,
        )

    def log_search(
        self,
        user_id: str,
        query: str,
        result_count: int,
        department: str | None = None,
    ) -> None:
        """Log a search query event."""
        self._insert_access_log(
            event_type="SEARCH",
            user_id=user_id,
            resource_type="CORTEX_SEARCH",
            resource_id="ENTERPRISE_KNOWLEDGE_SEARCH",
            action="SEARCH",
            department=department,
            outcome="SUCCESS",
            details={"query": query[:500], "result_count": result_count},
        )

    def log_ai_decision(
        self,
        conversation_id: str,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        guardrail_results: list[dict[str, Any]] | None = None,
    ) -> None:
        """Log an AI model invocation."""
        guardrail_json = "NULL"
        if guardrail_results:
            g_str = json.dumps(guardrail_results).replace("'", "''")
            guardrail_json = f"PARSE_JSON('{g_str}')"

        try:
            self.session.sql(f"""
                INSERT INTO GOVERNANCE.AI_GOVERNANCE_LOG (
                    EVENT_TYPE, CONVERSATION_ID, USER_ID, MODEL,
                    INPUT_TOKENS, OUTPUT_TOKENS, GUARDRAIL_RESULTS
                ) VALUES (
                    'AI_INVOCATION', '{conversation_id}', '{user_id}',
                    '{model}', {input_tokens}, {output_tokens}, {guardrail_json}
                )
            """).collect()
        except Exception as e:
            logger.warning(f"Failed to log AI decision: {e}")

    def log_guardrail_violation(
        self,
        conversation_id: str,
        user_id: str,
        violation_type: str,
        violation_details: str,
        action_taken: str,
    ) -> None:
        """Log a guardrail violation."""
        escaped_details = violation_details.replace("'", "''")[:5000]

        try:
            self.session.sql(f"""
                INSERT INTO GOVERNANCE.AI_GOVERNANCE_LOG (
                    EVENT_TYPE, CONVERSATION_ID, USER_ID,
                    VIOLATION_TYPE, VIOLATION_DETAILS, ACTION_TAKEN
                ) VALUES (
                    'GUARDRAIL_VIOLATION', '{conversation_id}', '{user_id}',
                    '{violation_type}', '{escaped_details}', '{action_taken}'
                )
            """).collect()
        except Exception as e:
            logger.warning(f"Failed to log guardrail violation: {e}")

    def _insert_access_log(
        self,
        event_type: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        department: str | None,
        outcome: str,
        details: dict[str, Any] | None,
    ) -> None:
        """Insert a record into ACCESS_AUDIT_LOG."""
        dept_sql = f"'{department}'" if department else "NULL"
        details_sql = "NULL"
        if details:
            d_str = json.dumps(details).replace("'", "''")
            details_sql = f"PARSE_JSON('{d_str}')"

        try:
            self.session.sql(f"""
                INSERT INTO GOVERNANCE.ACCESS_AUDIT_LOG (
                    EVENT_TYPE, USER_ID, USER_ROLE, RESOURCE_TYPE,
                    RESOURCE_ID, DEPARTMENT, ACTION, OUTCOME, DETAILS
                ) VALUES (
                    '{event_type}', '{user_id}', CURRENT_ROLE(),
                    '{resource_type}', '{resource_id}', {dept_sql},
                    '{action}', '{outcome}', {details_sql}
                )
            """).collect()
        except Exception as e:
            logger.warning(f"Failed to insert access audit log: {e}")
