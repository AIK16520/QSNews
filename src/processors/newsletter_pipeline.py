"""
Newsletter Processing Pipeline
Orchestrates newsletter fetching, processing, and storage.
"""

import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session

from fetchers.newsletter_fetcher import fetch_newsletters_from_gmail
from fetchers.newsletter_archive_scraper import scrape_newsletter_archive, scrape_all_archives
from processors.newsletter_processor import (
    generate_newsletter_summary,
    extract_newsletter_title,
    extract_newsletter_tags,
    extract_newsletter_industries
)
from utils.database import (
    Newsletter,
    get_session,
    init_database
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_duplicate_newsletter(session: Session, newsletter_data: Dict) -> bool:
    """
    Check if newsletter already exists in database.

    Checks by:
    1. Title + source + published_date
    2. Email subject + source + received_date
    """
    source = newsletter_data.get('source')
    title = extract_newsletter_title(newsletter_data)
    published_date = newsletter_data.get('published_date')
    received_date = newsletter_data.get('received_date')

    # Check by title/subject and date
    if published_date:
        existing = session.query(Newsletter).filter_by(
            source=source,
            title=title,
            published_date=published_date
        ).first()
        if existing:
            return True

    if received_date:
        existing = session.query(Newsletter).filter_by(
            source=source,
            title=title,
            received_date=received_date
        ).first()
        if existing:
            return True

    return False


def process_single_newsletter(
    session: Session,
    newsletter_data: Dict
) -> Optional[Newsletter]:
    """
    Process a single newsletter: generate summary and save to database.

    Args:
        session: Database session
        newsletter_data: Newsletter dictionary from fetcher/scraper

    Returns:
        Newsletter object if successful, None otherwise
    """
    source = newsletter_data.get('source', 'Unknown')

    # Check for duplicates
    if is_duplicate_newsletter(session, newsletter_data):
        logger.info(f"Skipping duplicate: {source}")
        return None

    try:
        # Extract title
        title = extract_newsletter_title(newsletter_data)

        # Generate AI summary with embedded links
        summary = generate_newsletter_summary(newsletter_data)

        # Extract tags using AI
        tags = extract_newsletter_tags(title, summary)
        
        # Extract industries using AI
        industries = extract_newsletter_industries(title, summary)

        # Create Newsletter object
        newsletter = Newsletter(
            title=title,
            source=source,
            published_date=newsletter_data.get('published_date'),
            summary=summary,
            full_content=newsletter_data.get('html_content'),
            plain_text=newsletter_data.get('plain_text'),
            extracted_links=newsletter_data.get('extracted_links', []),
            tags=tags,
            industries=industries,
            email_subject=newsletter_data.get('email_subject'),
            from_email=newsletter_data.get('from_email'),
            received_date=newsletter_data.get('received_date', datetime.utcnow()),
            fetched_date=datetime.utcnow(),
            status='not_included'
        )

        session.add(newsletter)
        return newsletter

    except Exception as e:
        logger.error(f"Error processing newsletter from {source}: {e}")
        return None


def fetch_and_process_gmail_newsletters(
    days_back: int = 7,
    limit: Optional[int] = None
) -> int:
    """
    Fetch newsletters from Gmail and process them.

    Args:
        days_back: How many days back to fetch
        limit: Maximum number to process

    Returns:
        Number of newsletters processed
    """
    session = get_session()
    processed_count = 0
    skipped_count = 0

    try:
        # Initialize database
        init_database()

        # Fetch from Gmail
        logger.info(f"Fetching newsletters from Gmail (past {days_back} days)")
        newsletters = fetch_newsletters_from_gmail(days_back=days_back, limit=limit)

        if not newsletters:
            logger.warning("No newsletters fetched from Gmail")
            return 0

        total = len(newsletters)
        logger.info(f"Processing {total} newsletters from Gmail...")

        # Process each newsletter
        for i, newsletter_data in enumerate(newsletters, 1):
            try:
                newsletter = process_single_newsletter(session, newsletter_data)

                if newsletter:
                    session.commit()
                    processed_count += 1
                    logger.info(f"[{i}/{total}] Processed: {newsletter.source} - {newsletter.title[:60]}")
                else:
                    skipped_count += 1
                    logger.info(f"[{i}/{total}] Skipped (duplicate)")

            except Exception as e:
                logger.error(f"Error processing newsletter {i}/{total}: {e}")
                session.rollback()
                skipped_count += 1
                continue

        logger.info(f"Gmail processing complete: {processed_count} added, {skipped_count} skipped")

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        session.rollback()
        raise

    finally:
        session.close()

    return processed_count


def scrape_and_process_archives(
    source_name: Optional[str] = None,
    days_back: int = 30
) -> int:
    """
    Scrape newsletter archives and process them.

    Args:
        source_name: Specific newsletter to scrape (None for all)
        days_back: How many days back to scrape

    Returns:
        Number of newsletters processed
    """
    session = get_session()
    processed_count = 0
    skipped_count = 0

    try:
        # Initialize database
        init_database()

        # Scrape archives
        if source_name:
            logger.info(f"Scraping archive for: {source_name}")
            newsletters_by_source = {source_name: scrape_newsletter_archive(source_name, days_back)}
        else:
            logger.info(f"Scraping all newsletter archives (past {days_back} days)")
            newsletters_by_source = scrape_all_archives(days_back)

        if not newsletters_by_source:
            logger.warning("No newsletters scraped from archives")
            return 0

        # Process all scraped newsletters
        for source, newsletters in newsletters_by_source.items():
            logger.info(f"\nProcessing {len(newsletters)} newsletters from {source}...")

            for i, newsletter_data in enumerate(newsletters, 1):
                try:
                    newsletter = process_single_newsletter(session, newsletter_data)

                    if newsletter:
                        session.commit()
                        processed_count += 1
                        logger.info(f"  [{i}/{len(newsletters)}] Processed: {newsletter.title[:60]}")
                    else:
                        skipped_count += 1
                        logger.info(f"  [{i}/{len(newsletters)}] Skipped (duplicate)")

                except Exception as e:
                    logger.error(f"  Error processing newsletter {i}/{len(newsletters)}: {e}")
                    session.rollback()
                    skipped_count += 1
                    continue

        logger.info(f"\nArchive processing complete: {processed_count} added, {skipped_count} skipped")

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        session.rollback()
        raise

    finally:
        session.close()

    return processed_count


def full_newsletter_pipeline(
    fetch_gmail: bool = True,
    scrape_archives: bool = True,
    gmail_days_back: int = 7,
    archive_days_back: int = 30
) -> Dict[str, int]:
    """
    Run complete newsletter pipeline: fetch Gmail + scrape archives.

    Returns:
        Dictionary with counts: {'gmail': N, 'archives': M, 'total': N+M}
    """
    logger.info("="*80)
    logger.info("NEWSLETTER PROCESSING PIPELINE")
    logger.info("="*80)

    gmail_count = 0
    archive_count = 0

    # 1. Fetch from Gmail
    if fetch_gmail:
        logger.info("\n--- STEP 1: Fetching from Gmail ---")
        gmail_count = fetch_and_process_gmail_newsletters(days_back=gmail_days_back)

    # 2. Scrape archives
    if scrape_archives:
        logger.info("\n--- STEP 2: Scraping Archives ---")
        archive_count = scrape_and_process_archives(days_back=archive_days_back)

    total = gmail_count + archive_count

    logger.info("\n" + "="*80)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"  Gmail: {gmail_count} newsletters")
    logger.info(f"  Archives: {archive_count} newsletters")
    logger.info(f"  Total: {total} newsletters added")
    logger.info("="*80)

    return {
        'gmail': gmail_count,
        'archives': archive_count,
        'total': total
    }


if __name__ == "__main__":
    # Test the pipeline
    print("\nRunning Newsletter Processing Pipeline...\n")

    # Run full pipeline
    results = full_newsletter_pipeline(
        fetch_gmail=True,
        scrape_archives=True,
        gmail_days_back=7,
        archive_days_back=30
    )

    print(f"\nPipeline Results: {results}")
