"""
Authentication and User Profile Router.
Adheres to SRP by handling HTTP concerns and delegating business logic to AuthService.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from nexusai.api.schemas import AuthRequest
from nexusai.services.auth_service import AuthService
from nexusai.api.dependencies import get_auth_service, get_current_user
from nexusai.db.models import User
from nexusai.core.exceptions import AuthenticationError, UserNotFoundError

router = APIRouter(tags=["Authentication"])


@router.post("/api/auth/signup")
def signup(req: AuthRequest, auth_service: AuthService = Depends(get_auth_service)):
    """User signup endpoint creating an isolated user profile with hashed password."""
    try:
        return auth_service.signup(email=req.email, password=req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/api/auth/login")
def login(req: AuthRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    User login endpoint verifying user registration and password hash.
    """
    try:
        return auth_service.login(email=req.email, password=req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (UserNotFoundError, AuthenticationError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/api/auth/demo-token")
def get_demo_token(email: str = "developer@nexusai.local", auth_service: AuthService = Depends(get_auth_service)):
    """Generates a valid JWT for the web client for rapid onboarding."""
    return auth_service.get_demo_token(email=email)


@router.get("/api/user/me")
def get_user_profile(user: User = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return {
        "user_id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
