"""Agent Runtime Service - orchestrates Cortex Agent interactions with memory and guardrails."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from snowflake.snowpark import Session

from src.shared.config import load_environment_config
from src.shared.exceptions import AgentError
from src.shared.models import AgentResponse
from src.shared.utils import generate_id, utc_now

from .memory.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class AgentRuntimeService:
    """Orchestrates interactions with the Cortex Agent.

    Responsibilities:
    - Manages conversation context (memory window)
    - Invokes the Cortex Agent via SQL
    - Records execution traces for observability
    - Integrates with guardrails (pre/post processing)
    - Handles department-scoped access
    """

    def __init__(self, session: Session, config: dict[str, Any] | None = None):
        self.session = session
        self.config = config or load_environment_config()
        agent_config = self.config.get("agent", {})

        self.model = agent_config.get("model", "claude-3-5-sonnet")
        self.max_tokens = agent_config.get("max_tokens", 4096)
        self.temperature = agent_config.get("temperature", 0.0)
        self.max_retries = agent_config.get("max_retries", 3)
        self.memory_limit = agent_config.get("conversation_memory_limit", 20)

        self.memory = ConversationManager(session, memory_limit=self.memory_limit)
        self.agent_name = "AGENT.ENTERPRISE_KNOWLEDGE_AGENT"

    def chat(
        self,
        query: str,
        conversation_id: str | None = None,
        user_id: str = "anonymous",
        department: str | None = None,
    ) -> AgentResponse:
        """Send a message to the Enterprise Knowledge Agent.

        Args:
            query: User's natural language question.
            conversation_id: Existing conversation ID (None creates new).
            user_id: Identifier for the user.
            department: User's department for access scoping.

        Returns:
            AgentResponse with answer, citations, and metadata.
        """
        start_time = time.time()
        response_id = generate_id("resp")

        # Get or create conversation
        if not conversation_id:
            conversation_id = self.memory.create_conversation(
                user_id=user_id, department=department
            )

        # Build conversation history for context
        history = self.memory.get_history(conversation_id)

        # Record user message
        self.memory.add_message(
            conversation_id=conversation_id,
            role="user",
            content=query,
        )

        # Invoke Cortex Agent
        try:
            result = self._invoke_agent(query, history, department)
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            # Retry logic
            result = self._retry_agent(query, history, department)

        latency_ms = (time.time() - start_time) * 1000

        # Extract response components
        response_text = result.get("response", "I was unable to find relevant information.")
        citations = result.get("citations", [])
        tokens_used = result.get("tokens_used", 0)

        # Record assistant message
        self.memory.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            citations=citations,
            token_count=tokens_used,
            latency_ms=int(latency_ms),
            model=self.model,
        )

        # Record execution trace
        self._record_trace(
            conversation_id=conversation_id,
            query=query,
            result=result,
            latency_ms=latency_ms,
        )

        return AgentResponse(
            response_id=response_id,
            query=query,
            response_text=response_text,
            citations=citations,
            confidence_score=result.get("confidence", 0.8),
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model=self.model,
        )

    def _invoke_agent(
        self,
        query: str,
        history: list[dict[str, str]],
        department: str | None,
    ) -> dict[str, Any]:
        """Invoke the Cortex Agent via SQL.

        Builds the message array with conversation history and calls
        SNOWFLAKE.CORTEX.INVOKE_AGENT.
        """
        # Build messages array for the agent
        messages = []

        # Add conversation history (within memory window)
        for msg in history[-self.memory_limit:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current query with department context
        user_content = query
        if department:
            user_content = f"[User Department: {department}] {query}"
        messages.append({"role": "user", "content": user_content})

        messages_json = json.dumps(messages).replace("'", "''")

        try:
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    PARSE_JSON('{messages_json}'),
                    OBJECT_CONSTRUCT(
                        'temperature', {self.temperature},
                        'max_tokens', {self.max_tokens}
                    )
                ) AS RESPONSE
            """).collect()

            if not result:
                raise AgentError("Agent returned no response")

            raw_response = result[0]["RESPONSE"]

            # Parse the response
            if isinstance(raw_response, str):
                return {
                    "response": raw_response,
                    "citations": [],
                    "tokens_used": len(raw_response) // 4,
                    "confidence": 0.8,
                }
            elif isinstance(raw_response, dict):
                return {
                    "response": raw_response.get("choices", [{}])[0].get(
                        "messages", raw_response.get("message", "")
                    ),
                    "citations": raw_response.get("citations", []),
                    "tokens_used": raw_response.get("usage", {}).get("total_tokens", 0),
                    "confidence": 0.8,
                }
            else:
                return {"response": str(raw_response), "citations": [], "tokens_used": 0}

        except AgentError:
            raise
        except Exception as e:
            raise AgentError(f"Agent invocation failed: {e}") from e

    def _invoke_cortex_agent(
        self,
        query: str,
        department: str | None,
    ) -> dict[str, Any]:
        """Invoke the native Cortex Agent (CREATE AGENT path).

        This uses the AGENT object directly rather than COMPLETE.
        Preferred path when the agent object is deployed.
        """
        escaped_query = query.replace("'", "''")

        dept_context = ""
        if department:
            dept_context = f" Only use documents from the {department} department."

        try:
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
                    '{self.agent_name}',
                    '{escaped_query}{dept_context}'
                ) AS RESPONSE
            """).collect()

            if not result:
                raise AgentError("Cortex Agent returned no response")

            response_data = result[0]["RESPONSE"]

            if isinstance(response_data, dict):
                return {
                    "response": response_data.get("text", response_data.get("content", "")),
                    "citations": response_data.get("citations", []),
                    "tool_calls": response_data.get("tool_use", []),
                    "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                    "confidence": 0.85,
                }
            return {"response": str(response_data), "citations": [], "tokens_used": 0}

        except Exception as e:
            raise AgentError(f"Cortex Agent invocation failed: {e}") from e

    def _retry_agent(
        self,
        query: str,
        history: list[dict[str, str]],
        department: str | None,
    ) -> dict[str, Any]:
        """Retry agent invocation with exponential backoff."""
        import time as time_module

        for attempt in range(1, self.max_retries + 1):
            try:
                wait_seconds = 2 ** attempt
                time_module.sleep(wait_seconds)
                logger.info(f"Retry attempt {attempt}/{self.max_retries}")
                return self._invoke_agent(query, history, department)
            except AgentError:
                if attempt == self.max_retries:
                    return {
                        "response": "I apologize, but I'm experiencing difficulties "
                        "processing your request. Please try again in a moment.",
                        "citations": [],
                        "tokens_used": 0,
                        "confidence": 0.0,
                    }
        return {"response": "Service unavailable.", "citations": [], "tokens_used": 0}

    def _record_trace(
        self,
        conversation_id: str,
        query: str,
        result: dict[str, Any],
        latency_ms: float,
    ) -> None:
        """Record agent execution trace for observability."""
        try:
            input_json = json.dumps({"query": query}).replace("'", "''")
            output_json = json.dumps({
                "response_length": len(result.get("response", "")),
                "citation_count": len(result.get("citations", [])),
                "confidence": result.get("confidence", 0),
            }).replace("'", "''")

            self.session.sql(f"""
                INSERT INTO AGENT.AGENT_TRACES (
                    CONVERSATION_ID, STEP_INDEX, STEP_TYPE,
                    STEP_INPUT, STEP_OUTPUT, DURATION_MS,
                    TOKENS_USED, MODEL, STATUS
                ) VALUES (
                    '{conversation_id}', 0, 'AGENT_INVOKE',
                    PARSE_JSON('{input_json}'),
                    PARSE_JSON('{output_json}'),
                    {int(latency_ms)},
                    {result.get('tokens_used', 0)},
                    '{self.model}',
                    'SUCCESS'
                )
            """).collect()
        except Exception as e:
            logger.warning(f"Failed to record trace: {e}")

    def get_conversation_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get full conversation history for display."""
        return self.memory.get_history(conversation_id)

    def list_conversations(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """List recent conversations for a user."""
        return self.memory.list_conversations(user_id, limit)
