"""Custom exceptions for the Enterprise AI Knowledge Platform."""

from __future__ import annotations


class PlatformError(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, error_code: str | None = None):
        self.error_code = error_code
        super().__init__(message)


class DocumentIngestionError(PlatformError):
    """Raised when document ingestion fails."""
    pass


class DocumentParsingError(PlatformError):
    """Raised when AI_PARSE_DOCUMENT fails."""
    pass


class ClassificationError(PlatformError):
    """Raised when document classification fails."""
    pass


class EmbeddingError(PlatformError):
    """Raised when embedding generation fails."""
    pass


class SearchError(PlatformError):
    """Raised when Cortex Search fails."""
    pass


class AgentError(PlatformError):
    """Raised when Agent execution fails."""
    pass


class GuardrailViolation(PlatformError):
    """Raised when a guardrail check fails."""

    def __init__(self, message: str, validator: str, score: float | None = None):
        self.validator = validator
        self.score = score
        super().__init__(message, error_code="GUARDRAIL_VIOLATION")


class ConfigurationError(PlatformError):
    """Raised for configuration-related errors."""
    pass


class AuthorizationError(PlatformError):
    """Raised when access is denied."""
    pass
