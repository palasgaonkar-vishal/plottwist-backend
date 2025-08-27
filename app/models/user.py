from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User model for authentication and user management.

    Attributes:
        id: Primary key
        email: Unique email address for login
        hashed_password: Bcrypt hashed password
        name: User's display name
        bio: User's biography/about section
        location: User's location
        website: User's website URL
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        refresh_token: Current JWT refresh token (nullable)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    refresh_token = Column(Text, nullable=True)

    # Relationships
    reviews = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )
    favorites = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
