#!/usr/bin/env python3
"""Upload sample documents to Snowflake stages for testing.

Usage:
    python scripts/upload_samples.py [--department finance]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.shared.session import get_session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample_documents"


def upload_department(session, department: str) -> int:
    """Upload all documents for a department to its stage."""
    dept_dir = SAMPLE_DIR / department
    if not dept_dir.exists():
        print(f"  [SKIP] No sample data for {department}")
        return 0

    stage_name = f"RAW.{department.upper()}_DOCS"
    count = 0

    for filepath in dept_dir.glob("*.txt"):
        doc_id = f"sample_{department}_{filepath.stem}"
        print(f"  Uploading {filepath.name} → @{stage_name}/{doc_id}/")

        session.file.put(
            str(filepath),
            f"@{stage_name}/{doc_id}/",
            auto_compress=False,
            overwrite=True,
        )

        # Register
        ext = filepath.suffix
        size = filepath.stat().st_size
        escaped_name = filepath.name.replace("'", "''")

        session.sql(f"""
            INSERT INTO RAW.DOCUMENT_REGISTRY (
                DOCUMENT_ID, FILE_NAME, FILE_TYPE, FILE_SIZE_BYTES,
                DEPARTMENT, STAGE_PATH, UPLOADED_BY, PROCESSING_STATUS
            ) VALUES (
                '{doc_id}', '{escaped_name}', '{ext}', {size},
                '{department}', '@{stage_name}/{doc_id}/{filepath.name}',
                'sample_data_loader', 'PENDING'
            )
        """).collect()
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Upload sample documents")
    parser.add_argument("--department", help="Single department to upload (default: all)")
    args = parser.parse_args()

    departments = [args.department] if args.department else [
        "finance", "treasury", "procurement", "risk", "compliance",
        "audit", "hr", "legal", "operations",
    ]

    print("Uploading sample documents to Snowflake stages...")
    print("=" * 60)

    total = 0
    with get_session(warehouse="CORTEX_AI_INGESTION_WH") as session:
        for dept in departments:
            print(f"\n[{dept.upper()}]")
            count = upload_department(session, dept)
            total += count

    print(f"\n{'=' * 60}")
    print(f"Uploaded {total} documents. Pipeline tasks will process them automatically.")


if __name__ == "__main__":
    main()
