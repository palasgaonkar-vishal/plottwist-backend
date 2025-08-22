from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import UserResponse
from app.schemas.user import UserUpdate
from app.services.user_service import UserService
from app.core.dependencies import get_current_active_user, get_current_verified_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of users to return"
    ),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """
    Get list of users with pagination.
    Requires verified user access.

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: Current verified user
        db: Database session

    Returns:
        List of users
    """
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get user by ID.
    Users can only access their own information unless they are verified.

    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated user
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found or access denied
    """
    user_service = UserService(db)

    # Users can access their own info, verified users can access others
    if user_id != current_user.id and not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update user information.
    Users can only update their own information.

    Args:
        user_id: User ID to update
        user_data: Updated user data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found or access denied
    """
    # Users can only update their own information
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    user_service = UserService(db)
    user = user_service.update_user(user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete user account (soft delete).
    Users can only delete their own account.

    Args:
        user_id: User ID to delete
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If user not found or access denied
    """
    # Users can only delete their own account
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    user_service = UserService(db)
    deleted = user_service.delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/{user_id}/verify", response_model=UserResponse)
def verify_user_email(
    user_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Verify a user's email address.
    Only verified users can verify other users.

    Args:
        user_id: User ID to verify
        current_user: Current verified user
        db: Database session

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    verified = user_service.verify_user_email(user_id)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user = user_service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Activate a user account.
    Only verified users can activate other users.

    Args:
        user_id: User ID to activate
        current_user: Current verified user
        db: Database session

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    activated = user_service.activate_user(user_id)

    if not activated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user = user_service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)
