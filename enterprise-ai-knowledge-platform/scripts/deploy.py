#!/usr/bin/env python3
"""Deployment script - executes SQL files in order against Snowflake."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from snowflake.connector import connect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"

EXECUTION_ORDER = [
    "schemas/001_create_database.sql",
    "schemas/002_create_schemas.sql",
    "roles/001_create_roles.sql",
    "roles/002_grant_privileges.sql",
    "stages/001_create_stages.sql",
    "tables/001_raw_tables.sql",
    "tables/002_processed_tables.sql",
    "tables/003_knowledge_tables.sql",
    "tables/004_agent_tables.sql",
    "tables/005_governance_tables.sql",
    "tables/006_observability_tables.sql",
    "policies/001_row_access_policies.sql",
    "policies/002_masking_policies.sql",
    "policies/003_tags.sql",
    "dynamic_tables/001_document_chunks.sql",
    "dynamic_tables/002_cost_aggregation.sql",
    "tasks/001_ingestion_pipeline.sql",
    "udfs/001_chunking_udf.sql",
    "cortex_search/001_create_service.sql",
    "agents/001_create_agent.sql",
]


def execute_sql_file(cursor, filepath: Path) -> None:
    """Execute a SQL file, splitting on semicolons."""
    content = filepath.read_text(encoding="utf-8")
    statements = [s.strip() for s in content.split(";") if s.strip()]
    for stmt in statements:
        print(f"  Executing: {stmt[:80]}...")
        cursor.execute(stmt)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy SQL objects to Snowflake")
    parser.add_argument("--account", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--role", default="CORTEX_AI_ADMIN")
    parser.add_argument("--warehouse", default="CORTEX_AI_INGESTION_WH")
    parser.add_argument("--authenticator", default="externalbrowser")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from-step", type=int, default=0)
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN - listing SQL execution order:")
        for i, path in enumerate(EXECUTION_ORDER):
            marker = ">>>" if i >= args.from_step else "   "
            print(f"  {marker} [{i:02d}] {path}")
        return 0

    conn = connect(
        account=args.account,
        user=args.user,
        role=args.role,
        warehouse=args.warehouse,
        authenticator=args.authenticator,
    )

    try:
        cursor = conn.cursor()
        for i, rel_path in enumerate(EXECUTION_ORDER):
            if i < args.from_step:
                continue
            filepath = SQL_DIR / rel_path
            if not filepath.exists():
                print(f"  [SKIP] {rel_path} (file not yet created)")
                continue
            print(f"[{i:02d}] Deploying: {rel_path}")
            execute_sql_file(cursor, filepath)
            print(f"  [OK]")
    except Exception as e:
        print(f"\n[ERROR] Failed at step {i}: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    print("\nDeployment complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
