"""Intent recognition and query planning for the agent."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from snowflake.snowpark import Session

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Recognized user intents."""
    SEARCH = "search"
    DISCOVERY = "discovery"
    DETAIL = "detail"
    COMPARISON = "comparison"
    ANALYTICS = "analytics"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"


@dataclass
class QueryPlan:
    """Execution plan for a user query."""
    intent: QueryIntent
    primary_tool: str
    secondary_tools: list[str]
    department_hint: str | None
    confidence: float
    reasoning: str


class IntentRecognizer:
    """Recognizes user intent and generates execution plans.

    Uses keyword heuristics for fast classification, with optional
    LLM-based classification for ambiguous queries.
    """

    # Intent keyword patterns
    SEARCH_KEYWORDS = {
        "find", "search", "look for", "where", "what does", "how does",
        "explain", "tell me about", "information on", "details about",
    }
    DISCOVERY_KEYWORDS = {
        "list", "show", "browse", "what documents", "available",
        "catalog", "overview", "what's in", "what do we have",
    }
    DETAIL_KEYWORDS = {
        "details", "metadata", "summary of", "tell me more",
        "expand on", "drill down", "specifics",
    }
    COMPARISON_KEYWORDS = {
        "compare", "difference", "versus", "vs", "contrast",
        "similarities", "how does X differ",
    }
    ANALYTICS_KEYWORDS = {
        "how many", "count", "statistics", "stats", "total",
        "trend", "most", "least", "average",
    }
    CONVERSATION_KEYWORDS = {
        "hello", "hi", "thanks", "thank you", "bye",
        "help", "what can you do", "who are you",
    }

    # Department detection patterns
    DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
        "finance": ["financial", "revenue", "budget", "fiscal", "accounting", "P&L"],
        "treasury": ["treasury", "cash", "liquidity", "FX", "hedging", "investment"],
        "procurement": ["procurement", "vendor", "supplier", "contract", "purchase", "RFP"],
        "risk": ["risk", "mitigation", "exposure", "VaR", "stress test", "scenario"],
        "compliance": ["compliance", "regulation", "regulatory", "SOX", "GDPR", "audit trail"],
        "audit": ["audit", "internal audit", "finding", "recommendation", "control"],
        "hr": ["HR", "employee", "benefit", "compensation", "recruitment", "policy"],
        "legal": ["legal", "contract", "agreement", "NDA", "liability", "litigation"],
        "operations": ["operations", "SLA", "process", "workflow", "incident", "KPI"],
    }

    def __init__(self, session: Session | None = None):
        self.session = session

    def recognize(self, query: str) -> QueryPlan:
        """Recognize intent and build execution plan for a query.

        Args:
            query: User's natural language query.

        Returns:
            QueryPlan with intent, tools, and confidence.
        """
        query_lower = query.lower().strip()

        # Detect department hint
        department = self._detect_department(query_lower)

        # Classify intent by keyword matching
        intent, confidence = self._classify_intent(query_lower)

        # Build tool plan
        plan = self._build_plan(intent, department, confidence, query_lower)

        logger.debug(
            f"Intent: {plan.intent.value}, "
            f"Tool: {plan.primary_tool}, "
            f"Dept: {plan.department_hint}, "
            f"Confidence: {plan.confidence:.2f}"
        )

        return plan

    def _classify_intent(self, query: str) -> tuple[QueryIntent, float]:
        """Classify query intent using keyword heuristics."""
        scores: dict[QueryIntent, float] = {
            QueryIntent.SEARCH: 0,
            QueryIntent.DISCOVERY: 0,
            QueryIntent.DETAIL: 0,
            QueryIntent.COMPARISON: 0,
            QueryIntent.ANALYTICS: 0,
            QueryIntent.CONVERSATION: 0,
        }

        for keyword in self.SEARCH_KEYWORDS:
            if keyword in query:
                scores[QueryIntent.SEARCH] += 1

        for keyword in self.DISCOVERY_KEYWORDS:
            if keyword in query:
                scores[QueryIntent.DISCOVERY] += 1

        for keyword in self.DETAIL_KEYWORDS:
            if keyword in query:
                scores[QueryIntent.DETAIL] += 1

        for keyword in self.COMPARISON_KEYWORDS:
            if keyword in query:
                scores[QueryIntent.COMPARISON] += 1

        for keyword in self.ANALYTICS_KEYWORDS:
            if keyword in query:
                scores[QueryIntent.ANALYTICS] += 1

        for keyword in self.CONVERSATION_KEYWORDS:
            if keyword in query:
                scores[QueryIntent.CONVERSATION] += 1

        # Find highest scoring intent
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]

        if max_score == 0:
            # Default to search for unrecognized queries
            return QueryIntent.SEARCH, 0.5

        # Normalize confidence
        total = sum(scores.values())
        confidence = max_score / total if total > 0 else 0.5

        return max_intent, min(confidence, 0.95)

    def _detect_department(self, query: str) -> str | None:
        """Detect department from query keywords."""
        for dept, keywords in self.DEPARTMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    return dept
        return None

    def _build_plan(
        self,
        intent: QueryIntent,
        department: str | None,
        confidence: float,
        query: str,
    ) -> QueryPlan:
        """Build execution plan based on recognized intent."""
        plans: dict[QueryIntent, dict[str, Any]] = {
            QueryIntent.SEARCH: {
                "primary": "search_knowledge",
                "secondary": ["get_document_details"],
                "reasoning": "User is searching for specific information",
            },
            QueryIntent.DISCOVERY: {
                "primary": "get_catalog",
                "secondary": ["get_department_stats"],
                "reasoning": "User wants to browse available knowledge",
            },
            QueryIntent.DETAIL: {
                "primary": "get_document_details",
                "secondary": ["get_document_metadata", "search_knowledge"],
                "reasoning": "User wants deep details about a specific document",
            },
            QueryIntent.COMPARISON: {
                "primary": "search_knowledge",
                "secondary": ["get_document_details"],
                "reasoning": "User wants to compare information across documents",
            },
            QueryIntent.ANALYTICS: {
                "primary": "get_department_stats",
                "secondary": ["get_catalog"],
                "reasoning": "User wants quantitative information",
            },
            QueryIntent.CONVERSATION: {
                "primary": "none",
                "secondary": [],
                "reasoning": "Conversational query, no tool needed",
            },
        }

        plan_config = plans.get(intent, plans[QueryIntent.SEARCH])

        return QueryPlan(
            intent=intent,
            primary_tool=plan_config["primary"],
            secondary_tools=plan_config["secondary"],
            department_hint=department,
            confidence=confidence,
            reasoning=plan_config["reasoning"],
        )
