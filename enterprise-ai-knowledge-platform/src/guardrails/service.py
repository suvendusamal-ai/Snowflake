"""Guardrails Engine - orchestrates pre/post validation of AI responses."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from snowflake.snowpark import Session

from src.shared.config import load_guardrails_config
from src.shared.exceptions import GuardrailViolation
from src.shared.models import GuardrailResult

from .validators.groundedness import GroundednessValidator
from .validators.pii_detector import PIIDetector
from .validators.injection_detector import InjectionDetector
from .validators.toxicity_detector import ToxicityDetector

logger = logging.getLogger(__name__)


@dataclass
class GuardrailsReport:
    """Aggregated results from all guardrail validators."""
    passed: bool
    results: list[GuardrailResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    blocked: bool = False
    modified_text: str | None = None


class GuardrailsEngine:
    """Orchestrates AI guardrail validations.

    Runs validators in sequence:
    1. Input guardrails (pre-agent): injection detection, PII in query
    2. Output guardrails (post-agent): groundedness, toxicity, PII in response

    Configuration-driven: validators can be enabled/disabled via config.
    """

    def __init__(self, session: Session, config: dict[str, Any] | None = None):
        self.session = session
        self.config = config or load_guardrails_config()
        validators_config = self.config.get("validators", {})

        # Initialize validators based on config
        self.groundedness = GroundednessValidator(
            session, validators_config.get("groundedness", {})
        )
        self.pii_detector = PIIDetector(
            validators_config.get("pii", {})
        )
        self.injection_detector = InjectionDetector(
            session, self.config.get("injection_detection", {})
        )
        self.toxicity_detector = ToxicityDetector(
            session, validators_config.get("toxicity", {})
        )

    def validate_input(self, query: str, user_id: str | None = None) -> GuardrailsReport:
        """Validate user input BEFORE sending to agent.

        Checks:
        - Prompt injection attempts
        - PII in user query (warn, don't block)
        """
        results: list[GuardrailResult] = []
        violations: list[str] = []

        # Check for prompt injection
        injection_config = self.config.get("injection_detection", {})
        if injection_config.get("enabled", True):
            injection_result = self.injection_detector.detect(query)
            results.append(injection_result)
            if not injection_result.passed:
                violations.append(
                    f"Prompt injection detected (score: {injection_result.score:.2f})"
                )

        # Check for PII in user query (informational, not blocking)
        pii_config = self.config.get("validators", {}).get("pii", {})
        if pii_config.get("enabled", True):
            pii_result = self.pii_detector.detect(query)
            results.append(pii_result)
            # PII in input is informational, logged but not blocked

        passed = len(violations) == 0
        blocked = not passed  # Block on injection attempts

        return GuardrailsReport(
            passed=passed,
            results=results,
            violations=violations,
            blocked=blocked,
        )

    def validate_output(
        self,
        response: str,
        context: str | None = None,
        query: str | None = None,
    ) -> GuardrailsReport:
        """Validate agent response AFTER generation.

        Checks:
        - Groundedness against retrieved context
        - PII leakage in response
        - Toxicity in response
        """
        results: list[GuardrailResult] = []
        violations: list[str] = []
        modified_text = response

        # Groundedness check (requires context)
        validators_config = self.config.get("validators", {})
        groundedness_config = validators_config.get("groundedness", {})
        if groundedness_config.get("enabled", True) and context:
            groundedness_result = self.groundedness.validate(
                response=response,
                context=context,
            )
            results.append(groundedness_result)
            if not groundedness_result.passed:
                violations.append(
                    f"Response not sufficiently grounded "
                    f"(score: {groundedness_result.score:.2f}, "
                    f"threshold: {groundedness_config.get('threshold', 0.8)})"
                )

        # PII detection in response
        pii_config = validators_config.get("pii", {})
        if pii_config.get("enabled", True):
            pii_result = self.pii_detector.detect(response)
            results.append(pii_result)
            if not pii_result.passed:
                # Mask PII in response
                modified_text = self.pii_detector.mask(response)
                violations.append(
                    f"PII detected in response: {pii_result.details.get('types_found', [])}"
                )

        # Toxicity check
        toxicity_config = validators_config.get("toxicity", {})
        if toxicity_config.get("enabled", True):
            toxicity_result = self.toxicity_detector.detect(response)
            results.append(toxicity_result)
            if not toxicity_result.passed:
                violations.append(
                    f"Toxicity detected: {toxicity_result.details.get('category', 'unknown')}"
                )

        passed = len(violations) == 0
        blocked = any(
            not r.passed and r.validator_name in ("toxicity", "injection")
            for r in results
        )

        return GuardrailsReport(
            passed=passed,
            results=results,
            violations=violations,
            blocked=blocked,
            modified_text=modified_text if modified_text != response else None,
        )

    def full_validation(
        self,
        query: str,
        response: str,
        context: str | None = None,
        user_id: str | None = None,
    ) -> GuardrailsReport:
        """Run both input and output validations. Merges results."""
        input_report = self.validate_input(query, user_id)
        if input_report.blocked:
            return input_report

        output_report = self.validate_output(response, context, query)

        # Merge
        all_results = input_report.results + output_report.results
        all_violations = input_report.violations + output_report.violations

        return GuardrailsReport(
            passed=len(all_violations) == 0,
            results=all_results,
            violations=all_violations,
            blocked=output_report.blocked,
            modified_text=output_report.modified_text,
        )
