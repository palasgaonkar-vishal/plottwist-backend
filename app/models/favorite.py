from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Favorite(Base):
    """
    Favorite model for tracking user's favorite books.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        book_id: Foreign key to Book
        created_at: Favorite creation timestamp
    """
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book_favorite'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, book_id={self.book_id})>" 