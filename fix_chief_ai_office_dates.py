#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix dates for Chief AI Office newsletters.
Sets dates in chronological order - most recent = today, going backwards daily.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.database import get_session, Newsletter, init_database
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_chief_ai_office_dates():
    """Fix dates for Chief AI Office newsletters."""
    session = get_session()

    try:
        # Initialize database
        init_database()

        logger.info("="*80)
        logger.info("FIXING CHIEF AI OFFICE NEWSLETTER DATES")
        logger.info("="*80)

        # Get all Chief AI Office newsletters ordered by ID (which should be scrape order)
        newsletters = session.query(Newsletter).filter_by(
            source='Chief AI Office'
        ).order_by(Newsletter.id).all()

        if not newsletters:
            logger.warning("No Chief AI Office newsletters found in database")
            return

        total = len(newsletters)
        logger.info(f"Found {total} Chief AI Office newsletters\n")

        # Start from today and go backwards
        today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # Set to 9 AM each day

        logger.info("Setting dates in chronological order (newest first):\n")

        # Reverse the list so most recent is first
        newsletters.reverse()

        for i, newsletter in enumerate(newsletters):
            # Calculate date: today minus i days
            new_date = today - timedelta(days=i)

            old_date = newsletter.published_date
            newsletter.published_date = new_date
            newsletter.received_date = new_date

            logger.info(f"[{i+1}/{total}] {newsletter.title[:50]}...")
            logger.info(f"  Old date: {old_date.strftime('%Y-%m-%d') if old_date else 'None'}")
            logger.info(f"  New date: {new_date.strftime('%Y-%m-%d')}\n")

        # Commit changes
        session.commit()

        # Summary
        logger.info("="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total newsletters: {total}")
        logger.info(f"Date range: {newsletters[-1].published_date.strftime('%Y-%m-%d')} to {newsletters[0].published_date.strftime('%Y-%m-%d')}")
        logger.info("="*80 + "\n")

        logger.info(f"✓ Successfully fixed dates for {total} Chief AI Office newsletters!")
        logger.info("  Dates now go from today backwards (daily intervals)")

    except Exception as e:
        logger.error(f"Error fixing dates: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    fix_chief_ai_office_dates()
