from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Favorite(Base):
    """
    Model for user favorite books.
    Tracks which books users have marked as favorites.
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorited_by")
    
    # Ensure a user can only favorite a book once
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="unique_user_book_favorite"),
    )

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, book_id={self.book_id})>"
