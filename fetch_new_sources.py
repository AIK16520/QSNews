"""
Fetch historic newsletters from newly added sources:
- TechCrunch
- TechCrunch Daily
- TechCrunch Startups Weekly
- Sequoia Capital
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.fetchers.newsletter_archive_scraper import scrape_newsletter_archive
from src.processors.newsletter_pipeline import scrape_and_process_archives
from src.utils.database import get_session
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_historic_newsletters(days_back: int = 30):
    """
    Fetch historic newsletters from new sources.

    Args:
        days_back: Number of days back to fetch (default: 30)
    """
    session = get_session()

    new_sources = [
        'Sequoia Capital'
    ]

    all_newsletters = {}

    try:
        for source in new_sources:
            logger.info(f"\n{'='*80}")
            logger.info(f"Fetching {source} newsletters from last {days_back} days...")
            logger.info(f"{'='*80}")

            newsletters = scrape_newsletter_archive(source, days_back=days_back)

            if newsletters:
                all_newsletters[source] = newsletters
                logger.info(f"✓ Fetched {len(newsletters)} newsletters from {source}")
            else:
                logger.warning(f"No newsletters found for {source}")

        # Process and save to database
        if all_newsletters:
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing and saving newsletters to database...")
            logger.info(f"{'='*80}\n")

            total_processed = 0
            total_duplicates = 0
            total_errors = 0

            for source, newsletters in all_newsletters.items():
                logger.info(f"Processing {len(newsletters)} newsletters from {source}...")

                for nl_data in newsletters:
                    try:
                        from src.processors.newsletter_pipeline import process_single_newsletter
                        result = process_single_newsletter(session, nl_data)

                        if result:
                            total_processed += 1
                            logger.info(f"  ✓ Processed: {nl_data['title'][:60]}")
                        else:
                            total_duplicates += 1
                            logger.info(f"  ↺ Duplicate/Skipped: {nl_data['title'][:60]}")

                    except Exception as e:
                        total_errors += 1
                        logger.error(f"  ✗ Error processing {nl_data.get('title', 'Unknown')[:60]}: {e}")

                session.commit()

            logger.info(f"\n{'='*80}")
            logger.info(f"SUMMARY")
            logger.info(f"{'='*80}")
            logger.info(f"Total fetched: {sum(len(nls) for nls in all_newsletters.values())}")
            logger.info(f"Successfully processed: {total_processed}")
            logger.info(f"Duplicates/Skipped: {total_duplicates}")
            logger.info(f"Errors: {total_errors}")
            logger.info(f"{'='*80}\n")

        else:
            logger.info("No newsletters to process")

    except Exception as e:
        logger.error(f"Error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fetch historic newsletters from newly added sources'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days back to fetch (default: 30)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("FETCHING NEWSLETTERS FROM NEW SOURCES")
    logger.info("="*80)
    logger.info(f"Sources: TechCrunch, Sequoia Capital")
    logger.info(f"Days back: {args.days}")
    logger.info("="*80 + "\n")

    fetch_historic_newsletters(days_back=args.days)

    logger.info("\n" + "="*80)
    logger.info("COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
