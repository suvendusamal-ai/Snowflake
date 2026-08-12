"""Shared utility functions."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier with optional prefix."""
    uid = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{uid}"
    return uid


def compute_checksum(content: bytes) -> str:
    """Compute SHA-256 checksum of content."""
    return hashlib.sha256(content).hexdigest()


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def truncate_text(text: str, max_chars: int = 2000) -> str:
    """Truncate text to max_chars at a sentence boundary when possible."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind(".")
    if last_period > max_chars * 0.7:
        return truncated[: last_period + 1]
    return truncated + "..."


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return len(text) // 4
