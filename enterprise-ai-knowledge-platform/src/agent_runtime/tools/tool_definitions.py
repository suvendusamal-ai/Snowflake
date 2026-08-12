"""Agent tools - callable functions for the agent runtime."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from snowflake.snowpark import Session

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None


class SearchTool:
    """Search the enterprise knowledge base."""

    NAME = "search_knowledge"

    def __init__(self, session: Session):
        self.session = session

    def execute(
        self,
        query: str,
        department: str | None = None,
        max_results: int = 10,
    ) -> ToolResult:
        """Execute knowledge base search."""
        try:
            escaped_query = query.replace("'", "''")
            dept_param = f"'{department}'" if department else "NULL"

            result = self.session.sql(f"""
                SELECT * FROM TABLE(
                    AGENT.SEARCH_KNOWLEDGE('{escaped_query}', {dept_param}, {max_results})
                )
            """).collect()

            results = [
                {
                    "chunk_id": row["CHUNK_ID"],
                    "document_id": row["DOCUMENT_ID"],
                    "text": row["CHUNK_TEXT"][:500],
                    "file_name": row["FILE_NAME"],
                    "department": row["DEPARTMENT"],
                    "section": row["SECTION_HEADER"],
                    "score": float(row["RELEVANCE_SCORE"]),
                }
                for row in result
            ]

            return ToolResult(tool_name=self.NAME, success=True, data=results)

        except Exception as e:
            return ToolResult(tool_name=self.NAME, success=False, error=str(e))


class CatalogTool:
    """Browse the knowledge catalog."""

    NAME = "get_catalog"

    def __init__(self, session: Session):
        self.session = session

    def execute(
        self,
        department: str | None = None,
        document_type: str | None = None,
    ) -> ToolResult:
        """Get catalog listing."""
        try:
            dept_param = f"'{department}'" if department else "NULL"
            type_param = f"'{document_type}'" if document_type else "NULL"

            result = self.session.sql(f"""
                SELECT * FROM TABLE(
                    AGENT.GET_CATALOG({dept_param}, {type_param})
                )
            """).collect()

            catalog = [
                {
                    "document_id": row["DOCUMENT_ID"],
                    "title": row["TITLE"],
                    "department": row["DEPARTMENT"],
                    "type": row["DOCUMENT_TYPE"],
                    "sensitivity": row["SENSITIVITY_LEVEL"],
                    "chunks": row["CHUNK_COUNT"],
                    "updated": row["LAST_UPDATED"],
                }
                for row in result
            ]

            return ToolResult(tool_name=self.NAME, success=True, data=catalog)

        except Exception as e:
            return ToolResult(tool_name=self.NAME, success=False, error=str(e))


class DocumentDetailsTool:
    """Get detailed information about a document."""

    NAME = "get_document_details"

    def __init__(self, session: Session):
        self.session = session

    def execute(self, document_id: str) -> ToolResult:
        """Get document details."""
        try:
            result = self.session.sql(f"""
                SELECT * FROM TABLE(
                    AGENT.GET_DOCUMENT_DETAILS('{document_id}')
                )
            """).collect()

            if not result:
                return ToolResult(
                    tool_name=self.NAME, success=True,
                    data={"error": "Document not found"}
                )

            row = result[0]
            return ToolResult(
                tool_name=self.NAME,
                success=True,
                data={
                    "document_id": row["DOCUMENT_ID"],
                    "file_name": row["FILE_NAME"],
                    "department": row["DEPARTMENT"],
                    "type": row["DOCUMENT_TYPE"],
                    "sensitivity": row["SENSITIVITY"],
                    "word_count": row["WORD_COUNT"],
                    "summary": row["SUMMARY"],
                    "topics": row["TOPICS"],
                },
            )

        except Exception as e:
            return ToolResult(tool_name=self.NAME, success=False, error=str(e))


class DepartmentStatsTool:
    """Get department-level statistics."""

    NAME = "get_department_stats"

    def __init__(self, session: Session):
        self.session = session

    def execute(self, department: str | None = None) -> ToolResult:
        """Get department statistics."""
        try:
            dept_param = f"'{department}'" if department else "NULL"

            result = self.session.sql(f"""
                SELECT * FROM TABLE(
                    AGENT.GET_DEPARTMENT_STATS({dept_param})
                )
            """).collect()

            stats = [
                {
                    "department": row["DEPARTMENT"],
                    "documents": row["DOCUMENT_COUNT"],
                    "chunks": row["TOTAL_CHUNKS"],
                    "avg_chunks_per_doc": float(row["AVG_CHUNKS_PER_DOC"] or 0),
                    "last_document": row["LAST_DOCUMENT_DATE"],
                }
                for row in result
            ]

            return ToolResult(tool_name=self.NAME, success=True, data=stats)

        except Exception as e:
            return ToolResult(tool_name=self.NAME, success=False, error=str(e))


class ToolRegistry:
    """Manages available tools for the agent."""

    def __init__(self, session: Session):
        self.session = session
        self.tools: dict[str, Any] = {
            SearchTool.NAME: SearchTool(session),
            CatalogTool.NAME: CatalogTool(session),
            DocumentDetailsTool.NAME: DocumentDetailsTool(session),
            DepartmentStatsTool.NAME: DepartmentStatsTool(session),
        }

    def get_tool(self, name: str) -> Any:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        """List all available tools."""
        return [
            {"name": name, "type": type(tool).__name__}
            for name, tool in self.tools.items()
        ]

    def execute_tool(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name with given parameters."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(tool_name=name, success=False, error=f"Tool '{name}' not found")
        return tool.execute(**kwargs)
