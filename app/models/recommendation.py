from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.database import Base


class RecommendationType(PyEnum):
    """Enumeration for different recommendation types"""
    CONTENT_BASED = "content_based"
    POPULARITY_BASED = "popularity_based"


class RecommendationFeedback(Base):
    """
    Model for tracking user feedback on recommendations.
    Used for analytics and improving recommendation algorithms.
    """
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type = Column(Enum(RecommendationType), nullable=False)
    is_positive = Column(Boolean, nullable=False)  # True for thumbs up, False for thumbs down
    context_data = Column(String(500), nullable=True)  # JSON string with additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    book = relationship("Book")

    def __repr__(self):
        feedback_type = "positive" if self.is_positive else "negative"
        return f"<RecommendationFeedback(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, type={self.recommendation_type.value}, feedback={feedback_type})>" 