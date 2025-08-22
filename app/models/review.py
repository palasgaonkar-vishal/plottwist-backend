from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Review(Base):
    """
    Review model for user book reviews and ratings.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        book_id: Foreign key to Book
        rating: User rating (1-5 scale)
        title: Optional review title
        content: Review text content
        created_at: Review creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="unique_user_book_review"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id = Column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating = Column(Float, nullable=False)  # 1.0 to 5.0 scale
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, rating={self.rating})>"

    @property
    def is_valid_rating(self) -> bool:
        """Check if the rating is within valid range (1-5)."""
        return 1.0 <= self.rating <= 5.0
