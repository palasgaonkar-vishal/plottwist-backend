from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
    get_password_hash,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, AuthResponse, UserResponse
from app.services.user_service import UserService


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    def register_user(self, user_data: UserRegister) -> AuthResponse:
        """
        Register a new user.

        Args:
            user_data: User registration data

        Returns:
            AuthResponse with user info and tokens

        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        existing_user = self.user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        # Generate tokens
        tokens = self._create_user_tokens(db_user.id)

        # Store refresh token
        db_user.refresh_token = tokens.refresh_token
        self.db.commit()

        # Return response
        user_response = UserResponse.model_validate(db_user)
        return AuthResponse(user=user_response, tokens=tokens)

    def login_user(self, user_data: UserLogin) -> AuthResponse:
        """
        Authenticate and login a user.

        Args:
            user_data: User login data

        Returns:
            AuthResponse with user info and tokens

        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        user = self.user_service.get_user_by_email(user_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled"
            )

        # Generate tokens
        tokens = self._create_user_tokens(user.id)

        # Store refresh token
        user.refresh_token = tokens.refresh_token
        self.db.commit()

        # Return response
        user_response = UserResponse.model_validate(user)
        return AuthResponse(user=user_response, tokens=tokens)

    def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New token pair

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        user_id = verify_token(refresh_token, token_type="refresh")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user and verify stored refresh token
        user = self.user_service.get_user_by_id(int(user_id))
        if not user or user.refresh_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled"
            )

        # Generate new tokens
        tokens = self._create_user_tokens(user.id)

        # Store new refresh token
        user.refresh_token = tokens.refresh_token
        self.db.commit()

        return tokens

    def logout_user(self, user_id: int) -> None:
        """
        Logout user by invalidating refresh token.

        Args:
            user_id: User ID to logout

        Raises:
            HTTPException: If user not found
        """
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Clear refresh token
        user.refresh_token = None
        self.db.commit()

    def get_current_user(self, access_token: str) -> Optional[User]:
        """
        Get current user from access token.

        Args:
            access_token: JWT access token

        Returns:
            User if token is valid, None otherwise
        """
        # Verify access token
        user_id = verify_token(access_token, token_type="access")
        if not user_id:
            return None

        # Get user
        user = self.user_service.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            return None

        return user

    def _create_user_tokens(self, user_id: int) -> Token:
        """
        Create access and refresh tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Token object with access and refresh tokens
        """
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
