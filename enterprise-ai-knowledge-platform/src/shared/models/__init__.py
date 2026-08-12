"""Shared Pydantic models used across modules."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Department(str, Enum):
    FINANCE = "finance"
    TREASURY = "treasury"
    PROCUREMENT = "procurement"
    RISK = "risk"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    HR = "hr"
    LEGAL = "legal"
    OPERATIONS = "operations"


class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DocumentType(str, Enum):
    POLICY = "policy"
    REPORT = "report"
    MEMO = "memo"
    CONTRACT = "contract"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    FORM = "form"
    CORRESPONDENCE = "correspondence"


class FileType(str, Enum):
    PDF = ".pdf"
    DOCX = ".docx"
    XLSX = ".xlsx"
    PPTX = ".pptx"
    CSV = ".csv"
    JSON = ".json"
    HTML = ".html"
    TXT = ".txt"
    PNG = ".png"
    JPG = ".jpg"


class DocumentMetadata(BaseModel):
    document_id: str = Field(description="Unique identifier for the document")
    file_name: str
    file_type: FileType
    file_size_bytes: int
    department: Department
    document_type: DocumentType | None = None
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    topics: list[str] = Field(default_factory=list)
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: str | None = None
    stage_path: str | None = None
    checksum: str | None = None


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    token_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    chunk_text: str
    score: float
    document_name: str
    department: Department
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    response_id: str
    query: str
    response_text: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence_score: float
    groundedness_score: float | None = None
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GuardrailResult(BaseModel):
    passed: bool
    validator_name: str
    score: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
