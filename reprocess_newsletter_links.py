"""
Re-process newsletter links to clean tracking URLs.
This script re-extracts links from existing newsletters using the improved link extractor.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_session, Newsletter
from src.utils.link_extractor import extract_and_explain_links
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reprocess_newsletter_links(dry_run: bool = True):
    """
    Re-extract links from all newsletters using improved link extractor.

    Args:
        dry_run: If True, only show what would be updated without saving
    """
    session = get_session()

    try:
        # Get all newsletters
        newsletters = session.query(Newsletter).all()

        logger.info(f"Found {len(newsletters)} newsletters to process")

        updated_count = 0
        no_content_count = 0
        no_change_count = 0

        for nl in newsletters:
            logger.info(f"\nProcessing: {nl.source} - {nl.title[:60]}")

            # Skip if no HTML content
            if not nl.full_content:
                logger.warning(f"  No HTML content available")
                no_content_count += 1
                continue

            # Extract links with improved extractor
            old_links = nl.extracted_links or []
            new_links = extract_and_explain_links(nl.full_content, source=nl.source)

            old_count = len(old_links)
            new_count = len(new_links)

            logger.info(f"  Old links: {old_count}, New links: {new_count}")

            # Show some example URLs if they changed
            if new_count > 0:
                logger.info(f"  Sample new links:")
                for link in new_links[:3]:
                    logger.info(f"    - {link['title'][:50]}")
                    logger.info(f"      URL: {link['url'][:100]}")

            # Update if there's a difference
            if old_count != new_count or old_links != new_links:
                if not dry_run:
                    nl.extracted_links = new_links
                    session.add(nl)
                    updated_count += 1
                    logger.info(f"  ✓ Updated links")
                else:
                    updated_count += 1
                    logger.info(f"  → Would update links")
            else:
                no_change_count += 1
                logger.info(f"  = No changes needed")

        if not dry_run:
            session.commit()
            logger.info(f"\n✓ Committed changes to database")

        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total newsletters: {len(newsletters)}")
        logger.info(f"Updated: {updated_count}")
        logger.info(f"No change: {no_change_count}")
        logger.info(f"No content: {no_content_count}")

        if dry_run:
            logger.info(f"\n⚠ DRY RUN - No changes saved. Run with --commit to save changes.")

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
        description='Re-process newsletter links to clean tracking URLs'
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Actually save changes (default is dry-run)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("RE-PROCESSING NEWSLETTER LINKS")
    logger.info("="*80)
    logger.info(f"Mode: {'COMMIT' if args.commit else 'DRY RUN'}")
    logger.info("="*80 + "\n")

    reprocess_newsletter_links(dry_run=not args.commit)

    logger.info("\n" + "="*80)
    logger.info("COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
