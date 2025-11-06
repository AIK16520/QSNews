"""
Deduplicator Module
Prevents duplicate articles from being added to the database.
"""

import logging
from sqlalchemy.orm import Session

from utils.database import Article

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_duplicate(session: Session, url: str) -> bool:
    """
    Check if an article with the given URL already exists in the database.

    Args:
        session: SQLAlchemy database session
        url: Article URL to check

    Returns:
        True if article exists, False otherwise
    """
    try:
        existing = session.query(Article).filter_by(url=url).first()
        is_dup = existing is not None

        if is_dup:
            logger.debug(f"Duplicate found: {url}")
        else:
            logger.debug(f"New article: {url}")

        return is_dup

    except Exception as e:
        logger.error(f"Error checking for duplicate {url}: {e}")
        # Conservative approach: assume not duplicate on error
        return False


def filter_duplicates(session: Session, articles: list) -> list:
    """
    Filter out duplicate articles from a list.

    Args:
        session: SQLAlchemy database session
        articles: List of article dictionaries with 'url' key

    Returns:
        List of non-duplicate articles
    """
    non_duplicates = []
    duplicate_count = 0

    for article in articles:
        url = article.get('url')
        if not url:
            logger.warning("Article missing URL, skipping")
            continue

        if not is_duplicate(session, url):
            non_duplicates.append(article)
        else:
            duplicate_count += 1

    logger.info(f"Filtered {duplicate_count} duplicates, {len(non_duplicates)} new articles")

    return non_duplicates


def get_duplicate_info(session: Session, url: str) -> dict:
    """
    Get information about a duplicate article if it exists.

    Args:
        session: SQLAlchemy database session
        url: Article URL

    Returns:
        Dictionary with duplicate info, or None if not found
    """
    try:
        existing = session.query(Article).filter_by(url=url).first()

        if existing:
            return {
                'id': existing.id,
                'title': existing.title,
                'source': existing.source,
                'fetched_date': existing.fetched_date,
                'status': existing.status
            }
        else:
            return None

    except Exception as e:
        logger.error(f"Error getting duplicate info for {url}: {e}")
        return None


if __name__ == "__main__":
    # Test deduplicator
    from utils.database import get_session, init_database

    print("Testing Deduplicator\n")

    # Initialize database
    init_database()
    session = get_session()

    try:
        # Test with sample URLs
        test_urls = [
            "https://example.com/article1",
            "https://example.com/article2",
            "https://example.com/article3"
        ]

        print("Testing duplicate detection:")
        for url in test_urls:
            is_dup = is_duplicate(session, url)
            print(f"  {url}: {'DUPLICATE' if is_dup else 'NEW'}")

        # Test filter function
        test_articles = [
            {'url': 'https://example.com/new1', 'title': 'New Article 1'},
            {'url': 'https://example.com/new2', 'title': 'New Article 2'},
        ]

        print(f"\nFiltering {len(test_articles)} articles:")
        filtered = filter_duplicates(session, test_articles)
        print(f"  Result: {len(filtered)} non-duplicates")

    finally:
        session.close()
