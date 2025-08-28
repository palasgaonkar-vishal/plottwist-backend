from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func, and_, extract
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.user import User
from app.models.review import Review
from app.models.favorite import Favorite
from app.schemas.user import UserCreate, UserUpdate, UserProfileStats
from app.core.security import get_password_hash, verify_password


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

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID (alias for get_user_by_id for backward compatibility).

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return self.get_user_by_id(user_id)

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

    def get_user_profile_stats(self, user_id: int) -> UserProfileStats:
        """Get comprehensive user profile statistics"""
        # Get total reviews count
        total_reviews = self.db.query(func.count(Review.id)).filter(
            Review.user_id == user_id
        ).scalar() or 0
        
        # Get average rating given by user
        avg_rating = self.db.query(func.avg(Review.rating)).filter(
            Review.user_id == user_id
        ).scalar()
        
        # Get total favorites count
        total_favorites = self.db.query(func.count(Favorite.id)).filter(
            Favorite.user_id == user_id
        ).scalar() or 0
        
        # Get unique books reviewed count
        books_reviewed = self.db.query(func.count(func.distinct(Review.book_id))).filter(
            Review.user_id == user_id
        ).scalar() or 0
        
        # Get reviews this month count
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        reviews_this_month = self.db.query(func.count(Review.id)).filter(
            and_(
                Review.user_id == user_id,
                Review.created_at >= current_month
            )
        ).scalar() or 0
        
        return UserProfileStats(
            total_reviews=total_reviews,
            average_rating_given=float(avg_rating) if avg_rating else None,
            total_favorites=total_favorites,
            books_reviewed=books_reviewed,
            reviews_this_month=reviews_this_month
        )

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def verify_user(self, user_id: int) -> bool:
        """Mark user as verified"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_verified = True
        self.db.commit()
        return True

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True

    def reactivate_user(self, user_id: int) -> bool:
        """Reactivate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.db.commit()
        return True

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True
