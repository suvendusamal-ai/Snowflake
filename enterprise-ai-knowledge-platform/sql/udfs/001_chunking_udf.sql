-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Chunking UDF: Splits text into semantic chunks (used by Dynamic Tables)
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA KNOWLEDGE;
USE WAREHOUSE CORTEX_AI_INGESTION_WH;

-- ============================================================================
-- CHUNK_DOCUMENT_UDF: Python UDTF that splits document text into chunks.
-- Returns an ARRAY of chunk texts that can be FLATTENed in downstream queries.
--
-- Parameters:
--   content (VARCHAR) - Full document text
--   chunk_size (NUMBER) - Target chars per chunk (default: 1500)
--   chunk_overlap (NUMBER) - Overlap chars between chunks (default: 200)
--
-- Returns: ARRAY of VARCHAR (each element is one chunk)
-- ============================================================================
CREATE OR REPLACE FUNCTION KNOWLEDGE.CHUNK_DOCUMENT_UDF(
    CONTENT VARCHAR,
    CHUNK_SIZE NUMBER DEFAULT 1500,
    CHUNK_OVERLAP NUMBER DEFAULT 200
)
RETURNS ARRAY
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
HANDLER = 'chunk_document'
AS $$
import re

def chunk_document(content, chunk_size, chunk_overlap):
    """Split document content into semantic chunks."""
    if not content or not content.strip():
        return []

    chunk_size = int(chunk_size)
    chunk_overlap = int(chunk_overlap)
    min_chunk_size = 100

    # Split on structural boundaries
    segments = re.split(r'\n{2,}', content)

    # Merge small segments to reach target chunk size
    merged = []
    current = ""

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        if current and len(current) + len(segment) + 2 > chunk_size:
            if len(current) >= min_chunk_size:
                merged.append(current)
            current = segment
        else:
            current = current + "\n\n" + segment if current else segment

    if current and len(current) >= min_chunk_size:
        merged.append(current)

    # If no structural boundaries found, fall back to fixed-size splitting
    if not merged and len(content) > chunk_size:
        start = 0
        while start < len(content):
            end = start + chunk_size
            if end < len(content):
                # Try to break at sentence boundary
                last_period = content[start:end].rfind('.')
                if last_period > chunk_size * 0.7:
                    end = start + last_period + 1
            chunk_text = content[start:end].strip()
            if chunk_text and len(chunk_text) >= min_chunk_size:
                merged.append(chunk_text)
            start = end - chunk_overlap
    elif not merged and content.strip():
        merged.append(content.strip())

    # Apply overlap
    chunks = []
    for i, text in enumerate(merged):
        if i > 0 and chunk_overlap > 0:
            prev = merged[i-1]
            overlap_text = prev[-chunk_overlap:]
            # Find sentence boundary in overlap
            last_period = overlap_text.rfind('.')
            if last_period > 0:
                overlap_text = overlap_text[last_period + 1:].strip()
            if overlap_text:
                text = overlap_text + "\n" + text
        chunks.append(text)

    return chunks
$$;

-- ============================================================================
-- Validate UDF works
-- ============================================================================
-- SELECT KNOWLEDGE.CHUNK_DOCUMENT_UDF(
--     'This is paragraph one about finance.\n\nThis is paragraph two about risk.\n\nThis is paragraph three.',
--     500, 100
-- );
