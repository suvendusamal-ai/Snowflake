"""Conversation memory manager - persists and retrieves chat history."""

from __future__ import annotations

import json
import logging
from typing import Any

from snowflake.snowpark import Session

from src.shared.utils import generate_id

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state and history in Snowflake tables.

    Provides:
    - Conversation lifecycle (create, close)
    - Message persistence (user, assistant, system, tool)
    - History retrieval with configurable window size
    - Conversation listing for UI
    """

    def __init__(self, session: Session, memory_limit: int = 20):
        self.session = session
        self.memory_limit = memory_limit

    def create_conversation(
        self,
        user_id: str,
        department: str | None = None,
        title: str | None = None,
    ) -> str:
        """Create a new conversation session.

        Returns:
            The new conversation_id.
        """
        conversation_id = generate_id("conv")
        title_val = f"'{title}'" if title else "NULL"
        dept_val = f"'{department}'" if department else "NULL"

        self.session.sql(f"""
            INSERT INTO AGENT.CONVERSATIONS (
                CONVERSATION_ID, USER_ID, DEPARTMENT, TITLE, STATUS
            ) VALUES (
                '{conversation_id}', '{user_id}', {dept_val}, {title_val}, 'ACTIVE'
            )
        """).collect()

        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        token_count: int | None = None,
        latency_ms: int | None = None,
        model: str | None = None,
    ) -> str:
        """Add a message to a conversation.

        Args:
            conversation_id: Target conversation.
            role: One of 'user', 'assistant', 'system', 'tool'.
            content: Message text content.
            citations: Source citations (for assistant messages).
            tool_calls: Tool call records (for assistant messages).
            token_count: Tokens used for this message.
            latency_ms: Response generation latency.
            model: Model that generated the response.

        Returns:
            The new message_id.
        """
        message_id = generate_id("msg")
        escaped_content = content.replace("'", "''")

        citations_sql = "NULL"
        if citations:
            citations_json = json.dumps(citations).replace("'", "''")
            citations_sql = f"PARSE_JSON('{citations_json}')"

        tool_calls_sql = "NULL"
        if tool_calls:
            tools_json = json.dumps(tool_calls).replace("'", "''")
            tool_calls_sql = f"PARSE_JSON('{tools_json}')"

        token_sql = str(token_count) if token_count else "NULL"
        latency_sql = str(latency_ms) if latency_ms else "NULL"
        model_sql = f"'{model}'" if model else "NULL"

        self.session.sql(f"""
            INSERT INTO AGENT.CONVERSATION_MESSAGES (
                MESSAGE_ID, CONVERSATION_ID, ROLE, CONTENT,
                CITATIONS, TOOL_CALLS, TOKEN_COUNT, LATENCY_MS, MODEL
            ) VALUES (
                '{message_id}', '{conversation_id}', '{role}',
                '{escaped_content}', {citations_sql}, {tool_calls_sql},
                {token_sql}, {latency_sql}, {model_sql}
            )
        """).collect()

        # Update conversation metadata
        self.session.sql(f"""
            UPDATE AGENT.CONVERSATIONS
            SET LAST_ACTIVITY_AT = CURRENT_TIMESTAMP(),
                MESSAGE_COUNT = MESSAGE_COUNT + 1
            WHERE CONVERSATION_ID = '{conversation_id}'
        """).collect()

        return message_id

    def get_history(
        self,
        conversation_id: str,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        """Get conversation message history.

        Args:
            conversation_id: Conversation to retrieve.
            limit: Max messages to return (defaults to memory_limit).

        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        limit = limit or self.memory_limit

        result = self.session.sql(f"""
            SELECT ROLE, CONTENT, CITATIONS, CREATED_AT
            FROM AGENT.CONVERSATION_MESSAGES
            WHERE CONVERSATION_ID = '{conversation_id}'
            ORDER BY CREATED_AT ASC
            LIMIT {limit}
        """).collect()

        return [
            {
                "role": row["ROLE"],
                "content": row["CONTENT"],
                "citations": row.get("CITATIONS"),
                "created_at": str(row["CREATED_AT"]),
            }
            for row in result
        ]

    def get_recent_context(
        self,
        conversation_id: str,
        window_size: int | None = None,
    ) -> list[dict[str, str]]:
        """Get the most recent messages for context injection.

        Returns only role + content for feeding into the agent prompt.
        """
        window = window_size or self.memory_limit

        result = self.session.sql(f"""
            SELECT ROLE, CONTENT
            FROM (
                SELECT ROLE, CONTENT, CREATED_AT
                FROM AGENT.CONVERSATION_MESSAGES
                WHERE CONVERSATION_ID = '{conversation_id}'
                ORDER BY CREATED_AT DESC
                LIMIT {window}
            )
            ORDER BY CREATED_AT ASC
        """).collect()

        return [{"role": row["ROLE"], "content": row["CONTENT"]} for row in result]

    def list_conversations(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent conversations for a user."""
        result = self.session.sql(f"""
            SELECT
                CONVERSATION_ID,
                TITLE,
                DEPARTMENT,
                MESSAGE_COUNT,
                STARTED_AT,
                LAST_ACTIVITY_AT,
                STATUS
            FROM AGENT.CONVERSATIONS
            WHERE USER_ID = '{user_id}'
            ORDER BY LAST_ACTIVITY_AT DESC
            LIMIT {limit}
        """).collect()

        return [
            {
                "conversation_id": row["CONVERSATION_ID"],
                "title": row["TITLE"],
                "department": row["DEPARTMENT"],
                "message_count": row["MESSAGE_COUNT"],
                "started_at": str(row["STARTED_AT"]),
                "last_activity": str(row["LAST_ACTIVITY_AT"]),
                "status": row["STATUS"],
            }
            for row in result
        ]

    def close_conversation(self, conversation_id: str) -> None:
        """Mark a conversation as closed."""
        self.session.sql(f"""
            UPDATE AGENT.CONVERSATIONS
            SET STATUS = 'CLOSED'
            WHERE CONVERSATION_ID = '{conversation_id}'
        """).collect()

    def generate_title(self, conversation_id: str) -> str:
        """Auto-generate a conversation title from the first user message."""
        result = self.session.sql(f"""
            SELECT CONTENT FROM AGENT.CONVERSATION_MESSAGES
            WHERE CONVERSATION_ID = '{conversation_id}' AND ROLE = 'user'
            ORDER BY CREATED_AT ASC
            LIMIT 1
        """).collect()

        if not result:
            return "New Conversation"

        first_message = result[0]["CONTENT"]
        # Use first 60 chars of first message as title
        title = first_message[:60].strip()
        if len(first_message) > 60:
            title += "..."

        escaped_title = title.replace("'", "''")
        self.session.sql(f"""
            UPDATE AGENT.CONVERSATIONS
            SET TITLE = '{escaped_title}'
            WHERE CONVERSATION_ID = '{conversation_id}'
        """).collect()

        return title
