from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """Service for handling user operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: Email address

        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get list of users with pagination.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of users
        """
        return self.db.query(User).offset(skip).limit(limit).all()

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        existing_user = self.get_user_by_email(user_data.email)
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

        return db_user

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User ID to update
            user_data: Updated user data

        Returns:
            Updated user if found, None otherwise

        Raises:
            HTTPException: If email already exists
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # Check if email is being updated and already exists
        if user_data.email and user_data.email != user.email:
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        # Update fields
        update_data = user_data.dict(exclude_unset=True)

        # Handle password hashing
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password")
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user (soft delete by setting is_active to False).

        Args:
            user_id: User ID to delete

        Returns:
            True if user was deleted, False if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        user.refresh_token = None  # Invalidate refresh token
        self.db.commit()

        return True

    def activate_user(self, user_id: int) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User ID to activate

        Returns:
            True if user was activated, False if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = True
        self.db.commit()

        return True

    def verify_user_email(self, user_id: int) -> bool:
        """
        Verify a user's email address.

        Args:
            user_id: User ID to verify

        Returns:
            True if user was verified, False if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_verified = True
        self.db.commit()

        return True
