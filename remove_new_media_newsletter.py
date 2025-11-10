#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to remove "What is New Media" newsletter from the database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.database import get_session, Newsletter, init_database
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def remove_new_media_newsletter():
    """Remove the 'What is New Media' newsletter from database."""
    session = get_session()

    try:
        # Initialize database
        init_database()

        logger.info("="*80)
        logger.info("REMOVING 'WHAT IS NEW MEDIA' NEWSLETTER")
        logger.info("="*80)

        # Search for the newsletter by title pattern
        newsletters = session.query(Newsletter).filter(
            Newsletter.title.ilike('%new media%')
        ).all()

        if not newsletters:
            logger.warning("No newsletters found matching 'New Media'")

            # Try alternative search
            logger.info("\nSearching for similar titles...")
            all_newsletters = session.query(Newsletter).all()
            for nl in all_newsletters:
                if 'media' in nl.title.lower() or 'news' in nl.title.lower():
                    logger.info(f"  Found: {nl.title} (ID: {nl.id}, Source: {nl.source})")
            return

        logger.info(f"Found {len(newsletters)} newsletter(s) matching 'New Media':\n")

        for nl in newsletters:
            logger.info(f"  ID: {nl.id}")
            logger.info(f"  Title: {nl.title}")
            logger.info(f"  Source: {nl.source}")
            logger.info(f"  Date: {nl.published_date.strftime('%Y-%m-%d') if nl.published_date else 'None'}")
            logger.info(f"  Status: {nl.status}")
            logger.info("")

        # Confirm deletion
        logger.info("Deleting newsletter(s)...\n")

        deleted_count = 0
        for nl in newsletters:
            logger.info(f"Deleting: {nl.title}")
            session.delete(nl)
            deleted_count += 1

        # Commit changes
        session.commit()

        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Deleted {deleted_count} newsletter(s)")
        logger.info("="*80 + "\n")

        logger.info(f"✓ Successfully removed 'What is New Media' newsletter from database!")

    except Exception as e:
        logger.error(f"Error removing newsletter: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    remove_new_media_newsletter()
