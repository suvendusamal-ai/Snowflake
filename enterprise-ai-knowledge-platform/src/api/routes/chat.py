"""Chat API endpoints - conversational AI interface."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.middleware.auth import get_current_user
from src.api.schemas import ChatRequest, ChatResponse, Citation, ErrorResponse
from src.shared.session import get_session

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def chat(request: Request, body: ChatRequest):
    """Send a message to the Enterprise Knowledge Agent.

    Returns an AI-generated response grounded in enterprise documents,
    with citations and confidence scoring.
    """
    user = get_current_user(request)
    start = time.time()

    try:
        with get_session(
            role=user.get("role", "CORTEX_AI_USER"),
            warehouse="CORTEX_AI_SEARCH_WH",
        ) as session:
            from src.agent_runtime import AgentRuntimeService
            from src.guardrails import GuardrailsEngine

            # Input guardrails
            guardrails = GuardrailsEngine(session)
            input_check = guardrails.validate_input(body.query, user["user_id"])
            if input_check.blocked:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Query blocked by guardrails",
                        "violations": input_check.violations,
                    },
                )

            # Agent invocation
            agent = AgentRuntimeService(session)
            response = agent.chat(
                query=body.query,
                conversation_id=body.conversation_id,
                user_id=user["user_id"],
                department=body.department or user.get("department"),
            )

            # Output guardrails
            output_check = guardrails.validate_output(
                response=response.response_text,
                context=None,  # Context already used by agent
                query=body.query,
            )

            final_text = output_check.modified_text or response.response_text
            latency = (time.time() - start) * 1000

            return ChatResponse(
                response_id=response.response_id,
                response_text=final_text,
                conversation_id=body.conversation_id or "new",
                citations=[
                    Citation(
                        document_id=c.get("document_id", ""),
                        file_name=c.get("file_name", ""),
                        section=c.get("section"),
                        score=c.get("score"),
                    )
                    for c in response.citations
                ],
                confidence_score=response.confidence_score,
                tokens_used=response.tokens_used,
                latency_ms=latency,
                guardrails_passed=output_check.passed,
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations(request: Request, limit: int = 20):
    """List recent conversations for the current user."""
    user = get_current_user(request)

    with get_session(role=user.get("role")) as session:
        from src.agent_runtime.memory import ConversationManager

        manager = ConversationManager(session)
        conversations = manager.list_conversations(user["user_id"], limit)
        return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation(request: Request, conversation_id: str):
    """Get full message history for a conversation."""
    user = get_current_user(request)

    with get_session(role=user.get("role")) as session:
        from src.agent_runtime.memory import ConversationManager

        manager = ConversationManager(session)
        messages = manager.get_history(conversation_id, limit=100)
        return {"conversation_id": conversation_id, "messages": messages}
