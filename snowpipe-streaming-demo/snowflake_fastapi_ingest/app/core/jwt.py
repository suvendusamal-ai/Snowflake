from jwt import InvalidTokenError, decode
from fastapi import HTTPException, status

from app.config import settings


def validate_jwt_token(token: str) -> dict:
    try:
        payload = decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT token.",
        ) from exc

    return payload
