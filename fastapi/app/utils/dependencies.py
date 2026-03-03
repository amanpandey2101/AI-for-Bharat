"""
Request dependencies — JWT extraction and current user resolution.

Migrated from SQLAlchemy to DynamoDB (UserRepository).
"""

from fastapi import Depends, HTTPException, status, Request
import jwt
import logging
from app.config import settings
from app.models.user import UserModel, UserRepository

logger = logging.getLogger(__name__)


def get_current_user_id(request: Request) -> str:
    """Extract the user ID from the JWT — checks Authorization header first, then cookie."""
    token = None

    # 1. Try Authorization: Bearer <token> header (works cross-domain, no cookie issues)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        logger.info("[Auth] Token found in Authorization header")

    # 2. Fall back to cookie (works when frontend/backend are same-site)
    if not token:
        token = request.cookies.get(settings.JWT_ACCESS_COOKIE_NAME)
        if token:
            logger.info("[Auth] Token found in cookie")

    if not token:
        logger.warning("[Auth] No token found in header or cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(user_id: str = Depends(get_current_user_id)) -> UserModel:
    """Resolve the full UserModel from the JWT user ID via DynamoDB."""
    user = UserRepository.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
