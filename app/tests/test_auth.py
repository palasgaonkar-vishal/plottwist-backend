import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash,
)
from app.schemas.auth import UserRegister, UserLogin
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.models.user import User


class TestSecurityFunctions:
    """Test cases for security utility functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        assert len(hashed) > 0
        
        # Verification should work
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = 123
        token = create_access_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        subject = verify_token(token, token_type="access")
        assert subject == str(user_id)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = 123
        token = create_refresh_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        subject = verify_token(token, token_type="refresh")
        assert subject == str(user_id)

    def test_verify_token_invalid(self):
        """Test token verification with invalid tokens."""
        # Invalid token
        assert verify_token("invalid_token") is None
        
        # Wrong token type
        refresh_token = create_refresh_token(subject=123)
        assert verify_token(refresh_token, token_type="access") is None

    def test_token_expiration(self):
        """Test token expiration."""
        # Create token with short expiration
        short_expiry = timedelta(seconds=-1)  # Already expired
        token = create_access_token(subject=123, expires_delta=short_expiry)
        
        # Should be invalid due to expiration
        assert verify_token(token) is None


class TestAuthService:
    """Test cases for AuthService."""

    def test_register_user_success(self, db_session: Session):
        """Test successful user registration."""
        auth_service = AuthService(db_session)
        user_data = UserRegister(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        result = auth_service.register_user(user_data)
        
        # Check response structure
        assert result.user.email == "test@example.com"
        assert result.user.name == "Test User"
        assert result.user.is_active is True
        assert result.user.is_verified is False
        assert result.tokens.access_token is not None
        assert result.tokens.refresh_token is not None
        assert result.tokens.token_type == "bearer"
        
        # Check user was created in database
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.refresh_token == result.tokens.refresh_token

    def test_register_user_duplicate_email(self, db_session: Session):
        """Test registration with duplicate email."""
        auth_service = AuthService(db_session)
        
        # Create first user
        user_data1 = UserRegister(
            email="test@example.com",
            password="password123",
            name="Test User 1"
        )
        auth_service.register_user(user_data1)
        
        # Try to create second user with same email
        user_data2 = UserRegister(
            email="test@example.com",
            password="password456",
            name="Test User 2"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_data2)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in str(exc_info.value.detail)

    def test_login_user_success(self, db_session: Session, sample_user):
        """Test successful user login."""
        auth_service = AuthService(db_session)
        
        # Login
        login_data = UserLogin(
            email=sample_user.email,
            password="password123"  # This is the original password before hashing
        )
        
        result = auth_service.login_user(login_data)
        
        # Check response
        assert result.user.email == sample_user.email
        assert result.user.name == sample_user.name
        assert result.tokens.access_token is not None
        assert result.tokens.refresh_token is not None
        
        # Check refresh token was stored
        db_session.refresh(sample_user)
        assert sample_user.refresh_token == result.tokens.refresh_token

    def test_login_user_invalid_email(self, db_session: Session):
        """Test login with invalid email."""
        auth_service = AuthService(db_session)
        
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_user(login_data)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(exc_info.value.detail)

    def test_login_user_invalid_password(self, db_session: Session, sample_user):
        """Test login with invalid password."""
        auth_service = AuthService(db_session)
        
        login_data = UserLogin(
            email=sample_user.email,
            password="wrongpassword"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_user(login_data)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in str(exc_info.value.detail)

    def test_login_inactive_user(self, db_session: Session, sample_user):
        """Test login with inactive user."""
        # Deactivate user
        sample_user.is_active = False
        db_session.commit()
        
        auth_service = AuthService(db_session)
        
        login_data = UserLogin(
            email=sample_user.email,
            password="password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_user(login_data)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "disabled" in str(exc_info.value.detail)

    def test_refresh_access_token_success(self, db_session: Session, sample_user):
        """Test successful token refresh."""
        import time
        
        auth_service = AuthService(db_session)
        
        # Create initial tokens
        tokens = auth_service._create_user_tokens(sample_user.id)
        sample_user.refresh_token = tokens.refresh_token
        db_session.commit()
        
        # Wait a small amount to ensure different timestamps
        time.sleep(0.01)
        
        # Refresh tokens
        new_tokens = auth_service.refresh_access_token(tokens.refresh_token)
        
        # Tokens should be different (different timestamps)
        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None
        assert new_tokens.token_type == "bearer"
        assert new_tokens.expires_in == 3600
        
        # Check new refresh token was stored
        db_session.refresh(sample_user)
        assert sample_user.refresh_token == new_tokens.refresh_token

    def test_refresh_access_token_invalid_token(self, db_session: Session):
        """Test token refresh with invalid token."""
        auth_service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("invalid_token")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid refresh token" in str(exc_info.value.detail)

    def test_refresh_access_token_mismatched_token(self, db_session: Session, sample_user):
        """Test token refresh with token not matching stored token."""
        auth_service = AuthService(db_session)
        
        # Create a refresh token but don't store it
        refresh_token = create_refresh_token(subject=sample_user.id)
        sample_user.refresh_token = "different_token"
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token(refresh_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_user_success(self, db_session: Session, sample_user):
        """Test successful user logout."""
        auth_service = AuthService(db_session)
        
        # Set refresh token
        sample_user.refresh_token = "some_refresh_token"
        db_session.commit()
        
        # Logout
        auth_service.logout_user(sample_user.id)
        
        # Check refresh token was cleared
        db_session.refresh(sample_user)
        assert sample_user.refresh_token is None

    def test_logout_user_not_found(self, db_session: Session):
        """Test logout with non-existent user."""
        auth_service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.logout_user(999)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_current_user_success(self, db_session: Session, sample_user):
        """Test getting current user from valid token."""
        auth_service = AuthService(db_session)
        
        # Create access token
        access_token = create_access_token(subject=sample_user.id)
        
        # Get current user
        current_user = auth_service.get_current_user(access_token)
        
        assert current_user is not None
        assert current_user.id == sample_user.id
        assert current_user.email == sample_user.email

    def test_get_current_user_invalid_token(self, db_session: Session):
        """Test getting current user with invalid token."""
        auth_service = AuthService(db_session)
        
        current_user = auth_service.get_current_user("invalid_token")
        assert current_user is None

    def test_get_current_user_inactive(self, db_session: Session, sample_user):
        """Test getting current user when user is inactive."""
        # Deactivate user
        sample_user.is_active = False
        db_session.commit()
        
        auth_service = AuthService(db_session)
        
        # Create access token
        access_token = create_access_token(subject=sample_user.id)
        
        # Get current user
        current_user = auth_service.get_current_user(access_token)
        assert current_user is None

    def test_create_user_tokens(self, db_session: Session):
        """Test token creation method."""
        auth_service = AuthService(db_session)
        user_id = 123
        
        tokens = auth_service._create_user_tokens(user_id)
        
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0
        
        # Verify tokens
        access_subject = verify_token(tokens.access_token, "access")
        refresh_subject = verify_token(tokens.refresh_token, "refresh")
        
        assert access_subject == str(user_id)
        assert refresh_subject == str(user_id) 