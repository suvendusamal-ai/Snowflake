"""Semantic chunking service - splits documents into meaningful chunks."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    chunk_size: int = 1500
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    strategy: str = "semantic"


@dataclass
class Chunk:
    index: int
    text: str
    char_count: int
    token_count: int
    section_header: str | None = None
    page_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticChunker:
    """Splits document text into semantically coherent chunks.

    Strategy:
    1. Split on structural boundaries (headings, double newlines, page breaks)
    2. Merge small segments until chunk_size is reached
    3. Apply overlap between consecutive chunks for context continuity
    """

    HEADING_PATTERN = re.compile(
        r"^(?:#{1,6}\s+.+|[A-Z][A-Z\s]{3,}[A-Z]$|(?:\d+\.)+\s+.+)", re.MULTILINE
    )
    PAGE_BREAK_PATTERN = re.compile(r"\f|\-{3,}Page \d+\-{3,}", re.IGNORECASE)
    SECTION_BREAK_PATTERN = re.compile(r"\n{3,}")

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    def chunk_document(
        self,
        content: str,
        document_id: str | None = None,
    ) -> list[Chunk]:
        """Split document content into semantic chunks.

        Args:
            content: Full document text.
            document_id: Optional ID for logging.

        Returns:
            Ordered list of Chunk objects.
        """
        if not content or not content.strip():
            return []

        if self.config.strategy == "semantic":
            chunks = self._semantic_split(content)
        else:
            chunks = self._fixed_size_split(content)

        logger.info(
            f"Chunked document {document_id or 'unknown'}: "
            f"{len(chunks)} chunks from {len(content)} chars"
        )
        return chunks

    def _semantic_split(self, content: str) -> list[Chunk]:
        """Split on structural boundaries, then merge to target size."""
        # Step 1: Identify structural segments
        segments = self._split_into_segments(content)

        # Step 2: Merge small segments to reach target chunk size
        merged = self._merge_segments(segments)

        # Step 3: Apply overlap
        chunks = self._apply_overlap(merged)

        return chunks

    def _split_into_segments(self, content: str) -> list[dict[str, Any]]:
        """Split content into structural segments based on headings and breaks."""
        segments: list[dict[str, Any]] = []
        current_header: str | None = None
        current_page: int = 1

        # Split on page breaks first
        pages = self.PAGE_BREAK_PATTERN.split(content)

        for page_idx, page_content in enumerate(pages, start=1):
            # Split on section breaks (triple newlines)
            sections = self.SECTION_BREAK_PATTERN.split(page_content)

            for section in sections:
                if not section.strip():
                    continue

                # Check if section starts with a heading
                heading_match = self.HEADING_PATTERN.match(section.strip())
                if heading_match:
                    current_header = heading_match.group(0).strip()

                segments.append({
                    "text": section.strip(),
                    "header": current_header,
                    "page": page_idx,
                })

        return segments

    def _merge_segments(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge consecutive segments until they reach target chunk size."""
        if not segments:
            return []

        merged: list[dict[str, Any]] = []
        current_text = ""
        current_header = segments[0].get("header")
        current_page = segments[0].get("page", 1)

        for segment in segments:
            segment_text = segment["text"]

            # If adding this segment exceeds chunk_size, finalize current
            if (
                current_text
                and len(current_text) + len(segment_text) + 1 > self.config.chunk_size
            ):
                if len(current_text) >= self.config.min_chunk_size:
                    merged.append({
                        "text": current_text,
                        "header": current_header,
                        "page": current_page,
                    })
                current_text = segment_text
                current_header = segment.get("header") or current_header
                current_page = segment.get("page", current_page)
            else:
                if current_text:
                    current_text += "\n\n" + segment_text
                else:
                    current_text = segment_text
                if segment.get("header"):
                    current_header = segment["header"]

        # Don't forget the last segment
        if current_text and len(current_text) >= self.config.min_chunk_size:
            merged.append({
                "text": current_text,
                "header": current_header,
                "page": current_page,
            })

        return merged

    def _apply_overlap(self, merged: list[dict[str, Any]]) -> list[Chunk]:
        """Create final chunks with overlap between consecutive pieces."""
        chunks: list[Chunk] = []

        for i, segment in enumerate(merged):
            text = segment["text"]

            # Prepend overlap from previous chunk
            if i > 0 and self.config.chunk_overlap > 0:
                prev_text = merged[i - 1]["text"]
                overlap = prev_text[-self.config.chunk_overlap :]
                # Find sentence boundary in overlap
                last_period = overlap.rfind(".")
                if last_period > 0:
                    overlap = overlap[last_period + 1 :].strip()
                if overlap:
                    text = overlap + "\n" + text

            chunks.append(Chunk(
                index=i,
                text=text,
                char_count=len(text),
                token_count=len(text) // 4,
                section_header=segment.get("header"),
                page_number=segment.get("page"),
            ))

        return chunks

    def _fixed_size_split(self, content: str) -> list[Chunk]:
        """Simple fixed-size splitting with overlap (fallback strategy)."""
        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(content):
            end = start + self.config.chunk_size

            # Try to break at sentence boundary
            if end < len(content):
                last_period = content[start:end].rfind(".")
                if last_period > self.config.chunk_size * 0.7:
                    end = start + last_period + 1

            chunk_text = content[start:end].strip()
            if chunk_text and len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(Chunk(
                    index=index,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    token_count=len(chunk_text) // 4,
                ))
                index += 1

            start = end - self.config.chunk_overlap

        return chunks
