"""
Delete spam newsletters from database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_session, Newsletter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sources that are likely spam
SPAM_SOURCES = [
    'Gettheelevator',
    'Statnews',
    'Superhuman AI',
    'Simple',
    'Mail.Beehiiv',
    'Mindstream'
]


def delete_spam_newsletters(dry_run: bool = True):
    """
    Delete spam newsletters from database.

    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    session = get_session()

    try:
        # Get all newsletters from spam sources
        spam_newsletters = session.query(Newsletter).filter(
            Newsletter.source.in_(SPAM_SOURCES)
        ).all()

        logger.info(f"Found {len(spam_newsletters)} spam newsletters from sources: {', '.join(SPAM_SOURCES)}")

        if len(spam_newsletters) == 0:
            logger.info("No spam newsletters to delete")
            return

        # Show details
        for nl in spam_newsletters:
            logger.info(f"  - {nl.source}: {nl.title[:80]}")

        if not dry_run:
            # Delete them
            for nl in spam_newsletters:
                session.delete(nl)

            session.commit()
            logger.info(f"\n✓ Deleted {len(spam_newsletters)} spam newsletters")
        else:
            logger.info(f"\n→ Would delete {len(spam_newsletters)} spam newsletters")

        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Spam newsletters found: {len(spam_newsletters)}")
        logger.info(f"Sources: {', '.join(SPAM_SOURCES)}")

        if dry_run:
            logger.info(f"\n⚠ DRY RUN - No changes saved. Run with --commit to delete.")

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
        description='Delete spam newsletters from database'
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Actually delete (default is dry-run)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("DELETING SPAM NEWSLETTERS")
    logger.info("="*80)
    logger.info(f"Mode: {'COMMIT' if args.commit else 'DRY RUN'}")
    logger.info("="*80 + "\n")

    delete_spam_newsletters(dry_run=not args.commit)

    logger.info("\n" + "="*80)
    logger.info("COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
