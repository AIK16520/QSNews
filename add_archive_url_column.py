"""
Database Migration: Add archive_url column to newsletters table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate():
    """Add archive_url column to newsletters table."""
    engine = get_engine()

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(newsletters)"))
            columns = [row[1] for row in result]

            if 'archive_url' in columns:
                logger.info("Column 'archive_url' already exists in newsletters table")
                return

            # Add the column
            logger.info("Adding archive_url column to newsletters table...")
            conn.execute(text("ALTER TABLE newsletters ADD COLUMN archive_url VARCHAR(2048)"))
            conn.commit()

            logger.info("✓ Successfully added archive_url column to newsletters table")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DATABASE MIGRATION: Add archive_url column")
    print("="*80 + "\n")

    migrate()

    print("\n" + "="*80)
    print("MIGRATION COMPLETE")
    print("="*80 + "\n")
