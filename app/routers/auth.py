from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    AuthResponse,
    Token,
    RefreshTokenRequest,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister, db: Session = Depends(get_db)
) -> AuthResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        User information and authentication tokens

    Raises:
        HTTPException: If email is already registered
    """
    auth_service = AuthService(db)
    return auth_service.register_user(user_data)


@router.post("/login", response_model=AuthResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)) -> AuthResponse:
    """
    Authenticate user and return tokens.

    Args:
        user_data: User login credentials
        db: Database session

    Returns:
        User information and authentication tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    return auth_service.login_user(user_data)


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token request data
        db: Database session

    Returns:
        New token pair

    Raises:
        HTTPException: If refresh token is invalid
    """
    auth_service = AuthService(db)
    return auth_service.refresh_access_token(refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> None:
    """
    Logout current user by invalidating refresh token.

    Args:
        current_user: Current authenticated user
        db: Database session
    """
    auth_service = AuthService(db)
    auth_service.logout_user(current_user.id)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)


@router.get("/verify-token")
def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Verify if the current token is valid.

    Args:
        current_user: Current authenticated user

    Returns:
        Token verification status
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "message": "Token is valid",
    }
