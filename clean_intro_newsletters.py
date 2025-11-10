"""
Script to identify and delete intro/welcome newsletters from the database.
These are typically onboarding emails sent when you first subscribe.
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

# Patterns that indicate intro/welcome newsletters
# Focus on title and email subject only, not summary
INTRO_PATTERNS = [
    'welcome',
    'thanks for subscribing',
    'subscription confirmed',
    'confirm your',
    "you're in",
    "you're officially",
    'thank you for joining',
    'quick steps to get started',
    'subscription successful',
    'confirm your email',
    'action required',
    "here's what's next",
    "here's your access"
]


def is_intro_newsletter(newsletter: Newsletter) -> bool:
    """
    Check if a newsletter is an intro/welcome newsletter.

    Only checks title and email_subject for specific welcome/confirmation patterns.
    Does not check summary to avoid false positives.

    Returns:
        True if it's an intro newsletter, False otherwise
    """
    title_lower = newsletter.title.lower()
    email_subject_lower = (newsletter.email_subject or '').lower()

    # Check if any intro pattern is in the title or email subject
    for pattern in INTRO_PATTERNS:
        if pattern in title_lower or pattern in email_subject_lower:
            return True

    return False


def identify_intro_newsletters(session) -> list:
    """
    Identify all intro/welcome newsletters in the database.

    Returns:
        List of Newsletter objects that are intro newsletters
    """
    all_newsletters = session.query(Newsletter).all()
    intro_newsletters = []

    for newsletter in all_newsletters:
        if is_intro_newsletter(newsletter):
            intro_newsletters.append(newsletter)

    return intro_newsletters


def delete_intro_newsletters(session, intro_newsletters: list, dry_run: bool = True):
    """
    Delete intro/welcome newsletters from the database.

    Args:
        session: Database session
        intro_newsletters: List of Newsletter objects to delete
        dry_run: If True, only show what would be deleted without actually deleting
    """
    if not intro_newsletters:
        logger.info("No intro newsletters found to delete.")
        return 0

    logger.info(f"\nFound {len(intro_newsletters)} intro/welcome newsletters:")
    logger.info("=" * 100)

    for i, newsletter in enumerate(intro_newsletters, 1):
        try:
            # Handle unicode issues in output
            title = newsletter.title.encode('ascii', 'ignore').decode('ascii')
            source = newsletter.source.encode('ascii', 'ignore').decode('ascii')
            logger.info(f"{i}. [ID: {newsletter.id}] {source} - {title[:70]}")
        except:
            logger.info(f"{i}. [ID: {newsletter.id}] {newsletter.source} - [Unicode error in title]")

    logger.info("=" * 100)

    if dry_run:
        logger.info("\n*** DRY RUN MODE - No newsletters will be deleted ***")
        logger.info(f"Would delete {len(intro_newsletters)} newsletters")
        return 0
    else:
        # Actually delete
        logger.info(f"\nDeleting {len(intro_newsletters)} intro newsletters...")

        for newsletter in intro_newsletters:
            session.delete(newsletter)

        session.commit()
        logger.info(f"Successfully deleted {len(intro_newsletters)} intro newsletters")
        return len(intro_newsletters)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Clean intro/welcome newsletters from database')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete the newsletters (default is dry run)')
    args = parser.parse_args()

    session = get_session()

    try:
        # Identify intro newsletters
        logger.info("Scanning database for intro/welcome newsletters...")
        intro_newsletters = identify_intro_newsletters(session)

        # Delete or show what would be deleted
        deleted_count = delete_intro_newsletters(
            session,
            intro_newsletters,
            dry_run=not args.delete
        )

        if args.delete:
            logger.info(f"\nCleaning complete. Deleted {deleted_count} intro newsletters.")
        else:
            logger.info(f"\nTo actually delete these newsletters, run:")
            logger.info("python clean_intro_newsletters.py --delete")

    except Exception as e:
        logger.error(f"Error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
