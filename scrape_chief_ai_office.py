#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to scrape Chief AI Office newsletter archive and add to database.
Fetches the past newsletters from the RSS feed.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.fetchers.newsletter_archive_scraper import scrape_newsletter_archive
from src.processors.newsletter_pipeline import process_single_newsletter
from src.utils.database import get_session, init_database
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_chief_ai_office(days_back: int = 365):
    """
    Scrape Chief AI Office newsletters and add to database.

    Args:
        days_back: How many days back to fetch (default 365 for full history)
    """
    session = get_session()

    try:
        # Initialize database
        init_database()

        logger.info("="*80)
        logger.info("SCRAPING CHIEF AI OFFICE NEWSLETTER ARCHIVE")
        logger.info("="*80)

        # Scrape from RSS feed
        logger.info(f"\nFetching newsletters from past {days_back} days...")
        newsletters = scrape_newsletter_archive('Chief AI Office', days_back=days_back)

        if not newsletters:
            logger.warning("No newsletters fetched from Chief AI Office")
            return

        total = len(newsletters)
        logger.info(f"Found {total} newsletters to process\n")

        # Process each newsletter
        processed_count = 0
        skipped_count = 0

        for i, newsletter_data in enumerate(newsletters, 1):
            try:
                logger.info(f"[{i}/{total}] Processing: {newsletter_data.get('title', 'Untitled')[:60]}...")

                newsletter = process_single_newsletter(session, newsletter_data)

                if newsletter:
                    session.commit()
                    processed_count += 1
                    logger.info(f"  ✓ Added to database")
                else:
                    skipped_count += 1
                    logger.info(f"  ⊘ Skipped (duplicate or filtered)")

            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                session.rollback()
                skipped_count += 1
                continue

        # Summary
        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total newsletters found: {total}")
        logger.info(f"Successfully added: {processed_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info("="*80 + "\n")

        if processed_count > 0:
            logger.info(f"✓ Successfully added {processed_count} Chief AI Office newsletters to the database!")
        else:
            logger.info("No new newsletters were added (they may already exist in the database)")

    except Exception as e:
        logger.error(f"Error scraping Chief AI Office: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Scrape Chief AI Office newsletter archive'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=365,
        help='How many days back to fetch (default: 365 for full history)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum number of newsletters to fetch (default: 20)'
    )

    args = parser.parse_args()

    # Since we want to limit to 20, we'll estimate days needed
    # Chief AI Office posts ~3-4 times per week, so 20 newsletters ≈ 60 days
    if args.limit == 20:
        days_back = 60
        logger.info(f"Fetching approximately {args.limit} most recent newsletters (past {days_back} days)")
    else:
        days_back = args.days_back

    scrape_chief_ai_office(days_back=days_back)
