"""Authentication middleware - validates tokens and extracts user context."""

from __future__ import annotations

import logging
import os
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {"/api/v1/health", "/docs", "/redoc", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Token-based authentication middleware.

    Supports:
    - Snowflake OAuth tokens (from Streamlit in Snowflake)
    - API keys (for external service-to-service calls)
    - Bypass for SPCS internal health checks
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth in dev mode if configured
        if os.environ.get("DISABLE_AUTH", "false").lower() == "true":
            request.state.user = _dev_user()
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user = await self._validate_bearer_token(token)
        elif auth_header.startswith("ApiKey "):
            api_key = auth_header[7:]
            user = await self._validate_api_key(api_key)
        else:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid Authorization header"},
            )

        if not user:
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid or expired token"},
            )

        # Attach user context to request
        request.state.user = user
        return await call_next(request)

    async def _validate_bearer_token(self, token: str) -> dict[str, Any] | None:
        """Validate a Snowflake OAuth or JWT token.

        In production (SPCS), Snowflake handles OAuth.
        Here we validate the token structure and extract claims.
        """
        try:
            # For SPCS deployment, Snowflake injects user context via headers
            # In standalone mode, decode JWT
            import base64
            import json

            parts = token.split(".")
            if len(parts) == 3:
                # JWT format - decode payload
                payload = parts[1]
                padding = 4 - len(payload) % 4
                payload += "=" * padding
                decoded = base64.urlsafe_b64decode(payload)
                claims = json.loads(decoded)

                return {
                    "user_id": claims.get("sub", claims.get("username", "unknown")),
                    "role": claims.get("role", "CORTEX_AI_USER"),
                    "department": claims.get("department"),
                    "email": claims.get("email"),
                }

            return None

        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    async def _validate_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Validate an API key for service-to-service communication."""
        valid_keys = os.environ.get("API_KEYS", "").split(",")
        if api_key in valid_keys and api_key:
            return {
                "user_id": "service_account",
                "role": "CORTEX_AI_SERVICE",
                "department": None,
                "email": None,
            }
        return None


def _dev_user() -> dict[str, Any]:
    """Default user context for development mode."""
    return {
        "user_id": os.environ.get("SNOWFLAKE_USER", "dev_user"),
        "role": "CORTEX_AI_ADMIN",
        "department": None,
        "email": "dev@localhost",
    }


def get_current_user(request: Request) -> dict[str, Any]:
    """Extract current user from request state. Use in route dependencies."""
    return getattr(request.state, "user", _dev_user())
