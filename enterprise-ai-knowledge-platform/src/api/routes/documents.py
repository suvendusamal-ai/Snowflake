"""Document management endpoints - upload, status, listing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from src.api.middleware.auth import get_current_user
from src.api.schemas import DocumentListResponse, DocumentStatusResponse, DocumentUploadResponse
from src.shared.session import get_session

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    department: str = Form(...),
):
    """Upload a document for processing.

    The document will be staged, registered, and queued for the
    ingestion pipeline (parse → classify → chunk → embed → index).
    """
    user = get_current_user(request)

    # Validate file size (50MB max)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    try:
        import tempfile
        from pathlib import Path

        # Write to temp file for staging
        suffix = Path(file.filename or "upload").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        with get_session(
            role=user.get("role", "CORTEX_AI_SERVICE"),
            warehouse="CORTEX_AI_INGESTION_WH",
        ) as session:
            from src.document_intelligence.service import DocumentIntelligenceService

            service = DocumentIntelligenceService(session)
            result = service.ingest_document(
                file_path=tmp_path,
                department=department,
                uploaded_by=user["user_id"],
            )

            return DocumentUploadResponse(
                document_id=result.document_id,
                file_name=file.filename or "unknown",
                department=department,
                stage_path=result.stage_path,
                status=result.status,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        import os
        os.unlink(tmp_path)


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(request: Request, document_id: str):
    """Get processing status of a document."""
    user = get_current_user(request)

    with get_session(role=user.get("role")) as session:
        result = session.sql(f"""
            SELECT DOCUMENT_ID, FILE_NAME, DEPARTMENT, PROCESSING_STATUS,
                   ERROR_MESSAGE, UPLOAD_TIMESTAMP, LAST_PROCESSED_AT
            FROM RAW.DOCUMENT_REGISTRY
            WHERE DOCUMENT_ID = '{document_id}'
        """).collect()

        if not result:
            raise HTTPException(status_code=404, detail="Document not found")

        row = result[0]
        return DocumentStatusResponse(
            document_id=row["DOCUMENT_ID"],
            file_name=row["FILE_NAME"],
            department=row["DEPARTMENT"],
            processing_status=row["PROCESSING_STATUS"],
            error_message=row["ERROR_MESSAGE"],
            upload_timestamp=str(row["UPLOAD_TIMESTAMP"]),
            last_processed_at=str(row["LAST_PROCESSED_AT"]) if row["LAST_PROCESSED_AT"] else None,
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    department: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    """List documents with optional filters."""
    user = get_current_user(request)

    filters = ["1=1"]
    if department:
        filters.append(f"DEPARTMENT = '{department}'")
    if status:
        filters.append(f"PROCESSING_STATUS = '{status}'")

    where_clause = " AND ".join(filters)

    with get_session(role=user.get("role")) as session:
        result = session.sql(f"""
            SELECT DOCUMENT_ID, FILE_NAME, DEPARTMENT, PROCESSING_STATUS,
                   ERROR_MESSAGE, UPLOAD_TIMESTAMP, LAST_PROCESSED_AT
            FROM RAW.DOCUMENT_REGISTRY
            WHERE {where_clause}
            ORDER BY UPLOAD_TIMESTAMP DESC
            LIMIT {limit}
        """).collect()

        count_result = session.sql(f"""
            SELECT COUNT(*) AS CNT FROM RAW.DOCUMENT_REGISTRY WHERE {where_clause}
        """).collect()

        documents = [
            DocumentStatusResponse(
                document_id=row["DOCUMENT_ID"],
                file_name=row["FILE_NAME"],
                department=row["DEPARTMENT"],
                processing_status=row["PROCESSING_STATUS"],
                error_message=row["ERROR_MESSAGE"],
                upload_timestamp=str(row["UPLOAD_TIMESTAMP"]),
                last_processed_at=str(row["LAST_PROCESSED_AT"]) if row["LAST_PROCESSED_AT"] else None,
            )
            for row in result
        ]

        return DocumentListResponse(
            documents=documents,
            total_count=count_result[0]["CNT"],
        )
