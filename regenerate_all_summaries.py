"""
Regenerate all newsletter summaries to use cleaned links from extracted_links.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_session, Newsletter
from src.processors.newsletter_processor import generate_newsletter_summary
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def regenerate_all_summaries(dry_run: bool = True):
    """
    Regenerate all newsletter summaries using cleaned links.

    Args:
        dry_run: If True, only show what would be updated without saving
    """
    session = get_session()

    try:
        # Get all newsletters with links
        newsletters = session.query(Newsletter).all()

        logger.info(f"Regenerating summaries for {len(newsletters)} newsletters...")

        updated_count = 0

        for i, nl in enumerate(newsletters, 1):
            # Skip if no links
            if not nl.extracted_links:
                continue

            logger.info(f"\n[{i}/{len(newsletters)}] {nl.source} - {nl.title[:60]}")

            if not dry_run:
                try:
                    # Prepare newsletter data for summary generation
                    newsletter_data = {
                        'title': nl.title,
                        'email_subject': nl.email_subject,
                        'html_content': nl.full_content,
                        'plain_text': nl.plain_text,
                        'extracted_links': nl.extracted_links,  # Use cleaned links
                        'source': nl.source
                    }

                    new_summary = generate_newsletter_summary(newsletter_data)

                    nl.summary = new_summary
                    session.add(nl)
                    updated_count += 1
                    logger.info(f"  ✓ Regenerated summary ({len(new_summary)} chars)")

                except Exception as e:
                    logger.error(f"  ✗ Error: {e}")
                    continue
            else:
                updated_count += 1
                logger.info(f"  → Would regenerate summary")

        if not dry_run:
            session.commit()
            logger.info(f"\n✓ Committed changes to database")

        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total newsletters: {len(newsletters)}")
        logger.info(f"Summaries regenerated: {updated_count}")

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
        description='Regenerate all newsletter summaries with cleaned links'
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Actually save changes (default is dry-run)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("REGENERATING ALL SUMMARIES")
    logger.info("="*80)
    logger.info(f"Mode: {'COMMIT' if args.commit else 'DRY RUN'}")
    logger.info("="*80 + "\n")

    regenerate_all_summaries(dry_run=not args.commit)

    logger.info("\n" + "="*80)
    logger.info("COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
