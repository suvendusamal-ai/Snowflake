"""Groundedness validator - checks if response is supported by context."""

from __future__ import annotations

import json
import logging
from typing import Any

from snowflake.snowpark import Session

from src.shared.models import GuardrailResult

logger = logging.getLogger(__name__)


class GroundednessValidator:
    """Validates that AI responses are grounded in retrieved context.

    Uses CORTEX COMPLETE to evaluate each claim in the response against
    the provided context, producing a groundedness score.
    """

    def __init__(self, session: Session, config: dict[str, Any]):
        self.session = session
        self.threshold = config.get("threshold", 0.8)
        self.model = config.get("model", "claude-3-5-haiku")

    def validate(self, response: str, context: str) -> GuardrailResult:
        """Check if response is grounded in the provided context.

        Args:
            response: The AI-generated response to validate.
            context: The retrieved context that should support the response.

        Returns:
            GuardrailResult with score and claim-level details.
        """
        if not response or not context:
            return GuardrailResult(
                passed=True,
                validator_name="groundedness",
                score=1.0,
                details={"reason": "Empty response or context, skipping"},
            )

        prompt = f"""Evaluate whether the RESPONSE is supported by the CONTEXT.

CONTEXT:
{context[:4000]}

RESPONSE:
{response[:2000]}

For the response as a whole, determine what fraction of claims are directly supported by the context.

Return ONLY a JSON object:
{{"score": <float 0.0-1.0>, "unsupported_claims": [<list of claims not in context>], "assessment": "<one sentence>"}}
"""

        try:
            escaped_prompt = prompt.replace("'", "''")
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{escaped_prompt}'
                ) AS RESULT
            """).collect()

            if not result:
                return self._default_pass()

            raw = result[0]["RESULT"]
            return self._parse_result(raw)

        except Exception as e:
            logger.warning(f"Groundedness check failed: {e}. Defaulting to pass.")
            return self._default_pass()

    def _parse_result(self, raw_response: str) -> GuardrailResult:
        """Parse the LLM groundedness evaluation."""
        try:
            text = raw_response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            score = float(data.get("score", 0.8))
            unsupported = data.get("unsupported_claims", [])
            assessment = data.get("assessment", "")

            passed = score >= self.threshold

            return GuardrailResult(
                passed=passed,
                validator_name="groundedness",
                score=score,
                details={
                    "threshold": self.threshold,
                    "unsupported_claims": unsupported,
                    "assessment": assessment,
                },
                violations=[f"Unsupported: {c}" for c in unsupported] if not passed else [],
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse groundedness result: {e}")
            return self._default_pass()

    def _default_pass(self) -> GuardrailResult:
        """Default pass result when validation cannot complete."""
        return GuardrailResult(
            passed=True,
            validator_name="groundedness",
            score=None,
            details={"reason": "Validation unavailable, defaulting to pass"},
        )
