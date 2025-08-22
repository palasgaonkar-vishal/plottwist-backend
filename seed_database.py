#!/usr/bin/env python3
"""
Database seeding script for PlotTwist.

This script seeds the database with initial data including:
- Standard book genres
- Test users
- Sample books with covers
- Sample reviews and ratings
- Sample favorites

Usage:
    python seed_database.py [--clear]
    
Options:
    --clear    Clear all existing data before seeding (use with caution)
"""

import sys
import argparse
import logging
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine
from app.models import Base
from app.utils.seeder import DatabaseSeeder

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main function to seed the database."""
    parser = argparse.ArgumentParser(description="Seed the PlotTwist database")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing data before seeding (use with caution)",
    )
    args = parser.parse_args()

    try:
        # Create tables if they don't exist
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Create database session
        db = SessionLocal()

        try:
            seeder = DatabaseSeeder(db)

            if args.clear:
                logger.warning("Clearing all existing data...")
                seeder.clear_all_data()
                logger.info("Data cleared successfully")

            # Seed the database
            seeder.seed_all()
            logger.info("Database seeding completed successfully!")

        except IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
            db.rollback()
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            db.rollback()
            sys.exit(1)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to connect to database or create tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
