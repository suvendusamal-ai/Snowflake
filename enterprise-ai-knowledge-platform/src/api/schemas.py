"""API request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── Chat Schemas ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="User question")
    conversation_id: str | None = Field(None, description="Existing conversation ID")
    department: str | None = Field(None, description="Department scope for search")


class Citation(BaseModel):
    document_id: str
    file_name: str
    section: str | None = None
    chunk_text: str | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    response_id: str
    response_text: str
    conversation_id: str
    citations: list[Citation] = []
    confidence_score: float
    tokens_used: int
    latency_ms: float
    guardrails_passed: bool = True


# ─── Document Schemas ────────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    department: str
    stage_path: str
    status: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    file_name: str
    department: str
    processing_status: str
    error_message: str | None = None
    upload_timestamp: str
    last_processed_at: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatusResponse]
    total_count: int


# ─── Search Schemas ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    department: str | None = None
    sensitivity_max: str | None = None
    limit: int = Field(10, ge=1, le=50)


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    chunk_text: str
    file_name: str
    department: str
    section_header: str | None = None
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    result_count: int
    latency_ms: float


# ─── Catalog Schemas ─────────────────────────────────────────────────────────

class CatalogEntry(BaseModel):
    document_id: str
    title: str
    department: str
    document_type: str | None = None
    sensitivity_level: str | None = None
    chunk_count: int | None = None
    total_tokens: int | None = None
    last_updated: str | None = None


class CatalogResponse(BaseModel):
    entries: list[CatalogEntry]
    total_count: int


# ─── Admin/Health Schemas ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    snowflake_connected: bool
    timestamp: str


class PlatformStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    departments: list[dict[str, Any]]
    search_service_status: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    error_code: str | None = None
