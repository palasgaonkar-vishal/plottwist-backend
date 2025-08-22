from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

# Create HTTP Bearer security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user.

    Args:
        credentials: HTTP Bearer credentials containing the access token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user is not found
    """
    # Extract token from credentials
    token = credentials.credentials

    # Create auth service and get current user
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current verified user.

    Args:
        current_user: Current active user

    Returns:
        Current verified user

    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unverified user"
        )

    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to optionally get the current authenticated user.
    This doesn't raise an exception if no token is provided.

    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session

    Returns:
        Current authenticated user if token is valid, None otherwise
    """
    if not credentials:
        return None

    # Extract token from credentials
    token = credentials.credentials

    # Create auth service and get current user
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)

    return user
