"""
Regenerate summaries for newsletters that contain tracking URLs.
This ensures summaries use cleaned links instead of tracking URLs.
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_session, Newsletter
from src.processors.newsletter_processor import generate_newsletter_summary
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Tracking domains to detect
TRACKING_DOMAINS = [
    'marketing.statnews.com',
    'click.convertkit-mail',
    'email.mg.',
    'mandrillapp.com',
    'list-manage.com',
    'links.ml.',
    'go.redirectingat.com',
    'link.mail.',
    'link.gettheelevator.com'
]


def has_tracking_links(summary: str) -> bool:
    """Check if summary contains tracking links."""
    if not summary:
        return False

    for domain in TRACKING_DOMAINS:
        if domain in summary:
            return True

    return False


def regenerate_summaries(dry_run: bool = True):
    """
    Regenerate summaries for newsletters with tracking links.

    Args:
        dry_run: If True, only show what would be updated without saving
    """
    session = get_session()

    try:
        # Get all newsletters
        newsletters = session.query(Newsletter).all()

        logger.info(f"Checking {len(newsletters)} newsletters for tracking links in summaries...")

        to_update = []

        # Find newsletters with tracking links in summaries
        for nl in newsletters:
            if has_tracking_links(nl.summary):
                to_update.append(nl)

        logger.info(f"Found {len(to_update)} newsletters with tracking links in summaries")

        if len(to_update) == 0:
            logger.info("No newsletters need summary regeneration")
            return

        # Regenerate summaries
        updated_count = 0

        for i, nl in enumerate(to_update, 1):
            logger.info(f"\n[{i}/{len(to_update)}] Processing: {nl.source} - {nl.title[:60]}")

            # Show old summary snippet
            if nl.summary:
                # Find tracking link in summary
                for domain in TRACKING_DOMAINS:
                    if domain in nl.summary:
                        # Find the link
                        pattern = rf'https?://[^\s\)\]]*{re.escape(domain)}[^\s\)\]]*'
                        match = re.search(pattern, nl.summary)
                        if match:
                            logger.info(f"  Old tracking link: {match.group(0)[:100]}...")
                        break

            if not dry_run:
                # Regenerate summary with cleaned links
                try:
                    # Prepare newsletter data for summary generation
                    newsletter_data = {
                        'title': nl.title,
                        'email_subject': nl.email_subject,
                        'html_content': nl.full_content,
                        'plain_text': nl.plain_text,
                        'extracted_links': nl.extracted_links,  # Already cleaned
                        'source': nl.source
                    }

                    new_summary = generate_newsletter_summary(newsletter_data)

                    nl.summary = new_summary
                    session.add(nl)
                    updated_count += 1
                    logger.info(f"  ✓ Regenerated summary")

                except Exception as e:
                    logger.error(f"  ✗ Error regenerating summary: {e}")
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
        logger.info(f"With tracking links in summaries: {len(to_update)}")
        logger.info(f"Updated: {updated_count}")

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
        description='Regenerate summaries for newsletters with tracking links'
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Actually save changes (default is dry-run)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("REGENERATING SUMMARIES WITH CLEAN LINKS")
    logger.info("="*80)
    logger.info(f"Mode: {'COMMIT' if args.commit else 'DRY RUN'}")
    logger.info("="*80 + "\n")

    regenerate_summaries(dry_run=not args.commit)

    logger.info("\n" + "="*80)
    logger.info("COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
