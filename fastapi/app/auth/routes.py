"""
Authentication routes — migrated from SQLAlchemy to DynamoDB.

All database operations now go through UserRepository which wraps
DynamoDB put_item / get_item / query calls.
"""

from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from datetime import datetime, timedelta
import logging
import requests as http_requests  # renamed to avoid clash with fastapi.Request

from app.validators.auth_validators import RegisterSchema, LoginSchema
from app.models.user import UserModel, UserRepository
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_verification_token,
)
from app.utils.email import send_verification_email
from app.utils.dependencies import get_current_user_id
from app.config import settings

logger = logging.getLogger(__name__)
auth_router = APIRouter()


# ── Register ───────────────────────────────────────────────────────────────────

@auth_router.post("/register")
async def register(data: RegisterSchema):
    try:
        existing_user = UserRepository.get_by_email(data.email)

        if existing_user and existing_user.is_verified:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Email already registered."},
            )

        # Remove unverified user so we can re-create
        if existing_user and not existing_user.is_verified:
            UserRepository.delete(existing_user.email)

        hashed_password = get_password_hash(data.password)
        token = generate_verification_token()

        new_user = UserModel(
            email=data.email,
            name=data.name,
            password_hash=hashed_password,
            provider="email",
            verification_token=token,
            verification_token_expires=(
                datetime.utcnow() + timedelta(hours=24)
            ).isoformat(),
            is_verified=False,
        )

        UserRepository.create(new_user)

        verification_link = f"{settings.API_BASE_URL}/auth/verify-email?token={token}"
        await send_verification_email(new_user.email, verification_link)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Verification email sent. Please verify your account to login",
            },
        )

    except Exception:
        logger.error("Unexpected error during registration", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Something went wrong."},
        )


# ── Login ──────────────────────────────────────────────────────────────────────

@auth_router.post("/login")
def login(data: LoginSchema):
    try:
        user = UserRepository.get_by_email(data.email)

        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid email or password."},
            )

        if user.provider != "email":
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Please login using GitHub."},
            )

        if user.is_deleted:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Account has been deleted."},
            )

        if user.is_inactive:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Account is inactive."},
            )

        if not user.is_verified:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message": "Please verify your email before logging in.",
                },
            )

        if not verify_password(data.password, user.password_hash):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid email or password."},
            )

        access_token = create_access_token(identity=user.id)

        response = JSONResponse(
            status_code=200,
            content={"success": True, "message": "Login successful."},
        )
        response.set_cookie(
            key=settings.JWT_ACCESS_COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            path=settings.JWT_ACCESS_COOKIE_PATH,
        )

        return response

    except Exception:
        logger.error("Unexpected error during login", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Something went wrong."},
        )


# ── Email Verification ────────────────────────────────────────────────────────

@auth_router.get("/verify-email")
def verify_email(token: str = Query(None)):
    try:
        if not token:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Verification token is required.",
                },
            )

        user = UserRepository.get_by_verification_token(token)

        if not user:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Invalid or expired verification token.",
                },
            )

        if user.is_verified:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Email already verified."},
            )

        if user.verification_token_expires:
            expires = datetime.fromisoformat(user.verification_token_expires)
            if expires < datetime.utcnow():
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "Verification token has expired.",
                    },
                )

        # Mark as verified and clear token
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        UserRepository.update(user)

        return Response(
            content="Email verified successfully. You can now log in.",
            status_code=200,
            media_type="text/plain",
        )

    except Exception:
        logger.error("Unexpected error during email verification", exc_info=True)
        return Response(
            content="Something went wrong.",
            status_code=500,
            media_type="text/plain",
        )


# ── GitHub OAuth ───────────────────────────────────────────────────────────────

@auth_router.get("/github")
def github_login():
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=user:email"
    )
    return RedirectResponse(github_url)


@auth_router.get("/github/callback")
def github_callback(code: str = Query(None), state: str = Query(None)):
    try:
        if not code:
            return Response(
                content="Authorization code not provided.",
                status_code=400,
                media_type="text/plain",
            )

        # ── Integration flow (state starts with "integration:") ──────────
        if state and state.startswith("integration:"):
            from app.integrations.routes import handle_github_integration_callback
            return handle_github_integration_callback(code, state)

        # ── Normal login flow ────────────────────────────────────────────
        token_response = http_requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            return Response(
                content="Failed to obtain access token.",
                status_code=400,
                media_type="text/plain",
            )

        user_response = http_requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        github_user = user_response.json()

        github_id = str(github_user.get("id"))
        email = github_user.get("email")
        name = github_user.get("name") or github_user.get("login")
        avatar_url = github_user.get("avatar_url")

        if not email:
            emails_response = http_requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            emails = emails_response.json()
            primary_email = next(
                (e.get("email") for e in emails if e.get("primary")), None
            )
            email = primary_email

        if not email:
            return Response(
                content="Email not available from GitHub.",
                status_code=400,
                media_type="text/plain",
            )

        user = UserRepository.get_by_email(email)

        if user:
            if not user.github_id:
                user.github_id = github_id
                user.avatar_url = avatar_url
                user.provider = "github"
                user.is_verified = True
                UserRepository.update(user)
        else:
            user = UserModel(
                email=email,
                name=name,
                github_id=github_id,
                provider="github",
                avatar_url=avatar_url,
                is_verified=True,
            )
            UserRepository.create(user)

        jwt_token = create_access_token(identity=user.id)

        response = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
        response.set_cookie(
            key=settings.JWT_ACCESS_COOKIE_NAME,
            value=jwt_token,
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            path=settings.JWT_ACCESS_COOKIE_PATH,
        )

        return response

    except Exception as e:
        return Response(
            content=f"GitHub login failed: {str(e)}",
            status_code=500,
            media_type="text/plain",
        )


# ── Protected Route ────────────────────────────────────────────────────────────

@auth_router.get("/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    user = UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
    }
