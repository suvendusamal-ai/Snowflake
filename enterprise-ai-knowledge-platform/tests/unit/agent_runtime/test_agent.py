"""Unit tests for Agent Runtime - Intent Recognition and Service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.agent_runtime.planning.intent_recognizer import (
    IntentRecognizer,
    QueryIntent,
    QueryPlan,
)
from src.agent_runtime.tools.tool_definitions import ToolRegistry, ToolResult


class TestIntentRecognizer:
    """Tests for intent recognition."""

    @pytest.fixture
    def recognizer(self):
        return IntentRecognizer()

    def test_search_intent_detected(self, recognizer):
        plan = recognizer.recognize("Find information about Q4 revenue projections")
        assert plan.intent == QueryIntent.SEARCH
        assert plan.primary_tool == "search_knowledge"

    def test_discovery_intent_detected(self, recognizer):
        plan = recognizer.recognize("Show me all available documents in the catalog")
        assert plan.intent == QueryIntent.DISCOVERY
        assert plan.primary_tool == "get_catalog"

    def test_analytics_intent_detected(self, recognizer):
        plan = recognizer.recognize("How many documents do we have in total?")
        assert plan.intent == QueryIntent.ANALYTICS
        assert plan.primary_tool == "get_department_stats"

    def test_detail_intent_detected(self, recognizer):
        plan = recognizer.recognize("Give me the details and metadata for that document")
        assert plan.intent == QueryIntent.DETAIL
        assert plan.primary_tool == "get_document_details"

    def test_comparison_intent_detected(self, recognizer):
        plan = recognizer.recognize("Compare the risk policies versus compliance requirements")
        assert plan.intent == QueryIntent.COMPARISON

    def test_conversation_intent_detected(self, recognizer):
        plan = recognizer.recognize("Hello, what can you do?")
        assert plan.intent == QueryIntent.CONVERSATION
        assert plan.primary_tool == "none"

    def test_unknown_defaults_to_search(self, recognizer):
        plan = recognizer.recognize("xyz123 random gibberish")
        assert plan.intent == QueryIntent.SEARCH
        assert plan.confidence == 0.5

    def test_department_detection_finance(self, recognizer):
        plan = recognizer.recognize("Find the latest financial report for Q4")
        assert plan.department_hint == "finance"

    def test_department_detection_hr(self, recognizer):
        plan = recognizer.recognize("What are the employee benefit policies?")
        assert plan.department_hint == "hr"

    def test_department_detection_legal(self, recognizer):
        plan = recognizer.recognize("Show me the NDA agreement templates")
        assert plan.department_hint == "legal"

    def test_department_detection_risk(self, recognizer):
        plan = recognizer.recognize("What is our current risk exposure?")
        assert plan.department_hint == "risk"

    def test_no_department_for_general_query(self, recognizer):
        plan = recognizer.recognize("Find all documents uploaded last week")
        assert plan.department_hint is None

    def test_plan_has_secondary_tools(self, recognizer):
        plan = recognizer.recognize("Search for compliance regulations")
        assert len(plan.secondary_tools) > 0

    def test_confidence_range(self, recognizer):
        plan = recognizer.recognize("Find financial revenue data")
        assert 0.0 <= plan.confidence <= 1.0


class TestToolRegistry:
    """Tests for the tool registry."""

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    def test_registry_has_all_tools(self, mock_session):
        registry = ToolRegistry(mock_session)
        tools = registry.list_tools()
        assert len(tools) == 4
        tool_names = {t["name"] for t in tools}
        assert "search_knowledge" in tool_names
        assert "get_catalog" in tool_names
        assert "get_document_details" in tool_names
        assert "get_department_stats" in tool_names

    def test_get_existing_tool(self, mock_session):
        registry = ToolRegistry(mock_session)
        tool = registry.get_tool("search_knowledge")
        assert tool is not None

    def test_get_nonexistent_tool(self, mock_session):
        registry = ToolRegistry(mock_session)
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_execute_nonexistent_tool_returns_error(self, mock_session):
        registry = ToolRegistry(mock_session)
        result = registry.execute_tool("nonexistent")
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "not found" in result.error

    def test_execute_tool_with_sql_error(self, mock_session):
        mock_session.sql.return_value.collect.side_effect = Exception("SQL Error")
        registry = ToolRegistry(mock_session)
        result = registry.execute_tool("search_knowledge", query="test")
        assert result.success is False
        assert "SQL Error" in result.error


class TestConversationManager:
    """Tests for conversation memory."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.sql.return_value.collect.return_value = []
        return session

    def test_create_conversation_returns_id(self, mock_session):
        from src.agent_runtime.memory.conversation_manager import ConversationManager

        manager = ConversationManager(mock_session)
        conv_id = manager.create_conversation(user_id="test_user")
        assert conv_id.startswith("conv_")
        assert mock_session.sql.called

    def test_add_message_calls_insert(self, mock_session):
        from src.agent_runtime.memory.conversation_manager import ConversationManager

        manager = ConversationManager(mock_session)
        msg_id = manager.add_message(
            conversation_id="conv_123",
            role="user",
            content="Hello world",
        )
        assert msg_id.startswith("msg_")
        # Should have called sql twice (insert + update)
        assert mock_session.sql.call_count >= 2

    def test_get_history_returns_list(self, mock_session):
        from src.agent_runtime.memory.conversation_manager import ConversationManager

        mock_session.sql.return_value.collect.return_value = [
            {"ROLE": "user", "CONTENT": "Hello", "CITATIONS": None, "CREATED_AT": "2026-01-01"},
            {"ROLE": "assistant", "CONTENT": "Hi!", "CITATIONS": None, "CREATED_AT": "2026-01-01"},
        ]

        manager = ConversationManager(mock_session)
        history = manager.get_history("conv_123")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_memory_limit_respected(self, mock_session):
        from src.agent_runtime.memory.conversation_manager import ConversationManager

        manager = ConversationManager(mock_session, memory_limit=5)
        manager.get_history("conv_123", limit=5)

        # Check that LIMIT 5 was in the SQL
        sql_call = mock_session.sql.call_args[0][0]
        assert "LIMIT 5" in sql_call
