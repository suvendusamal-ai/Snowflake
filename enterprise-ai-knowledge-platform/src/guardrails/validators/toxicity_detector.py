"""Toxicity Detector - identifies harmful or inappropriate content."""

from __future__ import annotations

import json
import logging
from typing import Any

from snowflake.snowpark import Session

from src.shared.models import GuardrailResult

logger = logging.getLogger(__name__)


class ToxicityDetector:
    """Detects toxic, harmful, or inappropriate content using CORTEX COMPLETE.

    Categories checked:
    - Hate speech
    - Harassment
    - Self-harm content
    - Violence
    - Sexual content
    - Discrimination
    """

    def __init__(self, session: Session, config: dict[str, Any] | None = None):
        self.session = session
        config = config or {}
        self.enabled = config.get("enabled", True)
        self.model = config.get("model", "claude-3-5-haiku")
        self.categories = config.get("categories", [
            "hate_speech", "harassment", "self_harm", "violence",
        ])

    def detect(self, text: str) -> GuardrailResult:
        """Detect toxicity in text.

        Returns:
            GuardrailResult with toxicity assessment.
        """
        if not self.enabled or not text:
            return GuardrailResult(
                passed=True,
                validator_name="toxicity",
                score=0.0,
                details={"reason": "disabled or empty"},
            )

        # Short texts are unlikely to be toxic in enterprise context
        if len(text) < 20:
            return GuardrailResult(
                passed=True,
                validator_name="toxicity",
                score=0.0,
                details={"reason": "text too short for analysis"},
            )

        categories_str = ", ".join(self.categories)
        prompt = f"""Analyze this text for toxicity across these categories: {categories_str}.

Text: "{text[:2000]}"

Rate overall toxicity from 0.0 (safe) to 1.0 (highly toxic).
Return ONLY JSON: {{"score": <float>, "flagged_category": "<category or none>", "safe": <bool>}}"""

        try:
            escaped = prompt.replace("'", "''")
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model}', '{escaped}') AS R
            """).collect()

            if not result:
                return self._default_safe()

            raw = result[0]["R"].strip()
            if "```" in raw:
                raw = raw.split("```json")[-1].split("```")[0].strip() if "```json" in raw else raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)
            score = float(data.get("score", 0.0))
            is_safe = data.get("safe", True)
            category = data.get("flagged_category", "none")

            passed = is_safe and score < 0.5

            return GuardrailResult(
                passed=passed,
                validator_name="toxicity",
                score=score,
                details={
                    "category": category if not passed else "none",
                    "safe": is_safe,
                },
                violations=[f"Toxic content ({category})"] if not passed else [],
            )

        except Exception as e:
            logger.warning(f"Toxicity detection failed: {e}")
            return self._default_safe()

    def _default_safe(self) -> GuardrailResult:
        """Default safe result when detection fails."""
        return GuardrailResult(
            passed=True,
            validator_name="toxicity",
            score=0.0,
            details={"reason": "detection unavailable, defaulting to safe"},
        )
