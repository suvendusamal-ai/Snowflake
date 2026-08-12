"""PII Detector - regex-based detection and masking of personally identifiable information."""

from __future__ import annotations

import re
from typing import Any

from src.shared.models import GuardrailResult


class PIIDetector:
    """Detects and masks PII patterns in text using regex.

    Patterns detected:
    - Social Security Numbers (SSN)
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - IP addresses
    """

    DEFAULT_PATTERNS = {
        "ssn": {
            "regex": r"\b\d{3}-\d{2}-\d{4}\b",
            "mask": "***-**-{last4}",
            "action": "mask",
        },
        "email": {
            "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "mask": "****@****.***",
            "action": "mask",
        },
        "phone": {
            "regex": r"\b(?:\+1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "mask": "(***) ***-****",
            "action": "mask",
        },
        "credit_card": {
            "regex": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "mask": "****-****-****-{last4}",
            "action": "redact",
        },
        "ip_address": {
            "regex": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "mask": "***.***.***.***",
            "action": "mask",
        },
    }

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        self.enabled = config.get("enabled", True)

        # Build patterns from config or defaults
        self.patterns: dict[str, re.Pattern] = {}
        custom_patterns = config.get("patterns", [])

        if custom_patterns:
            for p in custom_patterns:
                self.patterns[p["type"]] = re.compile(p["regex"])
        else:
            for name, spec in self.DEFAULT_PATTERNS.items():
                self.patterns[name] = re.compile(spec["regex"])

    def detect(self, text: str) -> GuardrailResult:
        """Detect PII in text.

        Returns:
            GuardrailResult indicating whether PII was found.
        """
        if not self.enabled or not text:
            return GuardrailResult(
                passed=True,
                validator_name="pii",
                score=1.0,
                details={"types_found": []},
            )

        found_types: list[str] = []
        found_count = 0

        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                found_types.append(pii_type)
                found_count += len(matches)

        passed = len(found_types) == 0

        return GuardrailResult(
            passed=passed,
            validator_name="pii",
            score=1.0 if passed else 0.0,
            details={
                "types_found": found_types,
                "total_matches": found_count,
            },
            violations=[f"PII detected: {t}" for t in found_types],
        )

    def mask(self, text: str) -> str:
        """Replace detected PII with masked values.

        Returns:
            Text with PII patterns replaced by masks.
        """
        if not self.enabled or not text:
            return text

        masked = text

        for pii_type, pattern in self.patterns.items():
            spec = self.DEFAULT_PATTERNS.get(pii_type, {})
            mask_template = spec.get("mask", "****")

            def _replace(match: re.Match) -> str:
                value = match.group(0)
                if "{last4}" in mask_template:
                    digits = re.sub(r"[^0-9]", "", value)
                    return mask_template.replace("{last4}", digits[-4:] if len(digits) >= 4 else "****")
                return mask_template

            masked = pattern.sub(_replace, masked)

        return masked
