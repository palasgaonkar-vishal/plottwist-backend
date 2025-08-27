from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc, text
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import hashlib
from collections import Counter
import logging

from ..models.user import User
from ..models.book import Book, Genre
from ..models.review import Review
from ..models.favorite import Favorite
from ..models.recommendation import RecommendationFeedback, RecommendationType
from ..schemas.recommendation import (
    RecommendationFeedbackCreate, 
    RecommendationItem, 
    RecommendationResponse,
    RecommendationParameters,
    RecommendationStats
)

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.cache_duration = timedelta(hours=6)  # Cache recommendations for 6 hours

    def get_content_based_recommendations(
        self, 
        user_id: int, 
        params: RecommendationParameters
    ) -> List[RecommendationItem]:
        """
        Generate content-based recommendations based on user's favorite books and genres.
        """
        try:
            # Get user's favorite genres from their favorited books
            user_favorite_genres = (
                self.db.query(Genre.id, func.count(Genre.id).label('genre_count'))
                .join(Book.genres)
                .join(Favorite, Book.id == Favorite.book_id)
                .filter(Favorite.user_id == user_id)
                .group_by(Genre.id)
                .order_by(desc('genre_count'))
                .all()
            )

            if not user_favorite_genres:
                # Fallback to popular books if user has no favorites
                return self._get_fallback_recommendations(user_id, params, "content_based")

            # Get top genres (limit to top 5 to avoid over-specialization)
            top_genre_ids = [genre_id for genre_id, _ in user_favorite_genres[:5]]

            # Get user's already interacted books (favorites + reviewed books)
            user_books = set()
            if params.exclude_user_books:
                user_book_ids = (
                    self.db.query(Favorite.book_id)
                    .filter(Favorite.user_id == user_id)
                    .union(
                        self.db.query(Review.book_id)
                        .filter(Review.user_id == user_id)
                    )
                    .all()
                )
                user_books = {book_id for (book_id,) in user_book_ids}

            # Find books in similar genres that user hasn't interacted with
            query = (
                self.db.query(Book, func.avg(Review.rating).label('avg_rating'), func.count(Review.id).label('review_count'))
                .join(Book.genres)
                .outerjoin(Review, Book.id == Review.book_id)
                .filter(Genre.id.in_(top_genre_ids))
                .group_by(Book.id)
                .having(func.count(Review.id) >= 3)  # Minimum 3 reviews for reliability
            )

            if params.min_rating:
                query = query.having(func.avg(Review.rating) >= params.min_rating)

            if user_books:
                query = query.filter(~Book.id.in_(user_books))

            books = query.order_by(desc('avg_rating'), desc('review_count')).limit(params.limit).all()

            recommendations = []
            for book, avg_rating, review_count in books:
                # Calculate content-based score
                book_genres = {genre.id for genre in book.genres}
                genre_overlap = len(book_genres.intersection(set(top_genre_ids)))
                genre_score = genre_overlap / len(top_genre_ids) if top_genre_ids else 0
                
                # Combine genre similarity with quality metrics
                quality_score = (avg_rating / 5.0) * 0.7 + min(review_count / 100.0, 1.0) * 0.3
                final_score = genre_score * 0.6 + quality_score * 0.4

                # Generate explanation
                matched_genres = [genre.name for genre in book.genres if genre.id in top_genre_ids]
                reason = f"Similar to your favorites in {', '.join(matched_genres[:2])}"
                if len(matched_genres) > 2:
                    reason += f" and {len(matched_genres) - 2} other genre(s)"

                recommendations.append(RecommendationItem(
                    book=book,
                    score=round(final_score, 3),
                    reason=reason,
                    recommendation_type=RecommendationType.CONTENT_BASED
                ))

            return sorted(recommendations, key=lambda x: x.score, reverse=True)

        except Exception as e:
            logger.error(f"Error generating content-based recommendations for user {user_id}: {str(e)}")
            return self._get_fallback_recommendations(user_id, params, "content_based")

    def get_popularity_based_recommendations(
        self, 
        user_id: int, 
        params: RecommendationParameters
    ) -> List[RecommendationItem]:
        """
        Generate popularity-based recommendations using top-rated books.
        """
        try:
            # Get user's already interacted books to exclude them
            user_books = set()
            if params.exclude_user_books:
                user_book_ids = (
                    self.db.query(Favorite.book_id)
                    .filter(Favorite.user_id == user_id)
                    .union(
                        self.db.query(Review.book_id)
                        .filter(Review.user_id == user_id)
                    )
                    .all()
                )
                user_books = {book_id for (book_id,) in user_book_ids}

            # Get popular books based on ratings and review counts
            query = (
                self.db.query(
                    Book, 
                    func.avg(Review.rating).label('avg_rating'), 
                    func.count(Review.id).label('review_count'),
                    func.count(Favorite.id).label('favorite_count')
                )
                .outerjoin(Review, Book.id == Review.book_id)
                .outerjoin(Favorite, Book.id == Favorite.book_id)
                .group_by(Book.id)
                .having(func.count(Review.id) >= 1)  # FIXED: Reduced from 5 to 1 review minimum
            )

            if params.min_rating:
                query = query.having(func.avg(Review.rating) >= params.min_rating)

            if user_books:
                query = query.filter(~Book.id.in_(user_books))

            if params.genres:
                query = query.join(Book.genres).filter(Genre.id.in_(params.genres))

            books = query.order_by(
                desc('avg_rating'), 
                desc('review_count'), 
                desc('favorite_count')
            ).limit(params.limit).all()

            recommendations = []
            for book, avg_rating, review_count, favorite_count in books:
                # Calculate popularity score
                rating_score = avg_rating / 5.0 if avg_rating else 0
                review_score = min(review_count / 100.0, 1.0)  # Normalize review count
                favorite_score = min(favorite_count / 50.0, 1.0)  # Normalize favorite count
                
                # Weighted popularity score
                popularity_score = rating_score * 0.5 + review_score * 0.3 + favorite_score * 0.2

                # Generate explanation
                reason = f"Highly rated ({avg_rating:.1f}★) with {review_count} reviews"
                if favorite_count > 0:
                    reason += f" and {favorite_count} favorites"

                recommendations.append(RecommendationItem(
                    book=book,
                    score=round(popularity_score, 3),
                    reason=reason,
                    recommendation_type=RecommendationType.POPULARITY_BASED
                ))

            return sorted(recommendations, key=lambda x: x.score, reverse=True)

        except Exception as e:
            logger.error(f"Error generating popularity-based recommendations for user {user_id}: {str(e)}")
            return self._get_fallback_recommendations(user_id, params, "popularity_based")

    def _get_fallback_recommendations(
        self, 
        user_id: int, 
        params: RecommendationParameters, 
        rec_type: str
    ) -> List[RecommendationItem]:
        """
        Fallback recommendations when primary algorithms fail or have insufficient data.
        """
        try:
            # Get user's books to exclude
            user_books = set()
            if params.exclude_user_books:
                user_book_ids = (
                    self.db.query(Favorite.book_id)
                    .filter(Favorite.user_id == user_id)
                    .union(
                        self.db.query(Review.book_id)
                        .filter(Review.user_id == user_id)
                    )
                    .all()
                )
                user_books = {book_id for (book_id,) in user_book_ids}

            # Get top-rated books as fallback
            query = (
                self.db.query(Book, func.avg(Review.rating).label('avg_rating'), func.count(Review.id).label('review_count'))
                .outerjoin(Review, Book.id == Review.book_id)
                .group_by(Book.id)
                .having(func.count(Review.id) >= 1)
            )

            if user_books:
                query = query.filter(~Book.id.in_(user_books))

            books = query.order_by(desc('avg_rating'), desc('review_count')).limit(params.limit).all()

            recommendations = []
            for book, avg_rating, review_count in books:
                score = (avg_rating / 5.0) if avg_rating else 0
                reason = f"Trending book ({avg_rating:.1f}★)" if avg_rating else "Popular book"

                recommendations.append(RecommendationItem(
                    book=book,
                    score=round(score, 3),
                    reason=reason,
                    recommendation_type=RecommendationType(rec_type)
                ))

            return recommendations

        except Exception as e:
            logger.error(f"Error generating fallback recommendations: {str(e)}")
            return []

    def create_recommendation_feedback(
        self, 
        user_id: int, 
        feedback_data: RecommendationFeedbackCreate
    ) -> RecommendationFeedback:
        """
        Create recommendation feedback for analytics.
        """
        feedback = RecommendationFeedback(
            user_id=user_id,
            book_id=feedback_data.book_id,
            recommendation_type=feedback_data.recommendation_type,
            is_positive=feedback_data.is_positive,
            context_data=feedback_data.context_data
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_recommendation_stats(
        self, 
        recommendation_type: Optional[RecommendationType] = None
    ) -> List[RecommendationStats]:
        """
        Get recommendation system analytics and statistics.
        """
        query = self.db.query(RecommendationFeedback)
        
        if recommendation_type:
            query = query.filter(RecommendationFeedback.recommendation_type == recommendation_type)

        feedback_data = query.all()
        
        # Group by recommendation type
        stats_by_type = {}
        for feedback in feedback_data:
            rec_type = feedback.recommendation_type
            if rec_type not in stats_by_type:
                stats_by_type[rec_type] = {
                    'total_feedback': 0,
                    'positive_feedback': 0,
                    'negative_feedback': 0
                }
            
            stats_by_type[rec_type]['total_feedback'] += 1
            if feedback.is_positive:
                stats_by_type[rec_type]['positive_feedback'] += 1
            else:
                stats_by_type[rec_type]['negative_feedback'] += 1

        # Calculate statistics
        stats_list = []
        for rec_type, data in stats_by_type.items():
            total_feedback = data['total_feedback']
            positive_feedback = data['positive_feedback']
            
            feedback_rate = total_feedback / 100.0  # Assuming 100 recommendations generated
            positive_rate = positive_feedback / total_feedback if total_feedback > 0 else 0

            stats_list.append(RecommendationStats(
                recommendation_type=rec_type,
                total_generated=100,  # This would be tracked separately in a real system
                total_feedback=total_feedback,
                positive_feedback=positive_feedback,
                negative_feedback=data['negative_feedback'],
                feedback_rate=round(feedback_rate, 3),
                positive_rate=round(positive_rate, 3),
                avg_score=None  # Could calculate average recommendation scores
            ))

        return stats_list

    def _generate_cache_key(self, user_id: int, rec_type: str, params: RecommendationParameters) -> str:
        """
        Generate cache key for recommendations.
        """
        params_str = f"{params.limit}_{params.exclude_user_books}_{params.min_rating}_{params.genres}"
        cache_string = f"rec_{user_id}_{rec_type}_{params_str}"
        return hashlib.md5(cache_string.encode()).hexdigest()

    def invalidate_user_cache(self, user_id: int):
        """
        Invalidate cached recommendations for a user (e.g., when they add new favorites).
        """
        # In a real implementation, this would clear Redis/Memcached entries
        # For now, we'll just log the action
        logger.info(f"Cache invalidated for user {user_id}")
        pass 