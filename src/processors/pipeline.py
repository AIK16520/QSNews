"""
Processing Pipeline
Orchestrates the complete article processing workflow:
1. Load fetched articles
2. Filter duplicates
3. Scrape full content
4. Classify with LLM
5. Store in database
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from src.fetchers.rss_fetcher import load_fetched_articles
from src.fetchers.web_scraper import scrape_article_content
from src.processors.deduplicator import is_duplicate
from src.processors.classifier import classify_article
from src.processors.content_validator import validate_article_quality
from src.utils.database import (
    Article,
    get_session,
    get_or_create_category,
    get_or_create_industry,
    init_database
)

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_article(
    session: Session,
    article_data: Dict,
    scrape_delay: float = 2.0
) -> Optional[Article]:
    """
    Process a single article through the complete pipeline.

    Args:
        session: Database session
        article_data: Article dictionary from RSS fetch
        scrape_delay: Delay before scraping (for rate limiting)

    Returns:
        Article object if successful, None otherwise
    """
    url = article_data.get('url')
    title = article_data.get('title', 'Untitled')
    source = article_data.get('source', 'Unknown')

    # 1. Check for duplicates
    if is_duplicate(session, url):
        return None

    # 2. Scrape full content
    time.sleep(scrape_delay)  # Rate limiting

    full_content = scrape_article_content(url)

    if not full_content:
        # Fall back to RSS summary if scraping fails
        full_content = article_data.get('rss_summary', '')

    # 3. Validate content length
    if len(full_content) < config.MIN_ARTICLE_LENGTH:
        return None

    # 4. Validate content quality (check for bundled articles)
    validation_data = {
        'title': title,
        'summary': article_data.get('rss_summary', ''),
        'full_content': full_content
    }
    is_valid, reason = validate_article_quality(validation_data)
    if not is_valid:
        logger.warning(f"Article failed quality check: {reason} - {title[:60]}")
        return None

    # 5. Classify with LLM
    classification = classify_article(
        title=title,
        content=full_content,
        categories_list=config.CATEGORIES,
        industries_list=config.INDUSTRIES
    )

    # 6. Parse published date
    published_date = None
    if article_data.get('published_date'):
        try:
            from dateutil import parser
            published_date = parser.parse(article_data['published_date'])
        except:
            pass

    # 7. Get or create category
    category = get_or_create_category(session, classification['category'])
    if not category:
        category = get_or_create_category(session, 'General AI')

    # 8. Get industries
    industries = []
    for industry_name in classification['industries']:
        industry = get_or_create_industry(session, industry_name)
        if industry:
            industries.append(industry)

    if not industries:
        # Default to General AI if no valid industries
        default_industry = get_or_create_industry(session, 'General AI')
        if default_industry:
            industries.append(default_industry)

    # 9. Create Article object
    article = Article(
        url=url,
        title=title,
        source=source,
        published_date=published_date,
        summary=classification.get('summary', ''),
        full_content=full_content,
        category=category,
        fetched_date=datetime.utcnow(),
        status='not_included'
    )

    # 10. Assign industries (many-to-many)
    article.industries = industries

    # 11. Add to session
    session.add(article)

    return article


def process_articles(
    session: Optional[Session] = None,
    input_file: str = 'data/temp_fetched.json',
    scrape_delay: float = 2.0
) -> int:
    """
    Process all fetched articles through the complete pipeline.

    Args:
        session: Database session (creates new one if None)
        input_file: Path to fetched articles JSON file
        scrape_delay: Delay between scraping requests

    Returns:
        Number of articles successfully processed
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True

    processed_count = 0
    skipped_count = 0
    error_count = 0

    try:
        # Initialize database (creates tables, seeds data)
        init_database()

        # Load fetched articles
        logger.info(f"Loading articles from {input_file}")
        articles = load_fetched_articles(input_file)

        if not articles:
            logger.warning("No articles to process")
            return 0

        total = len(articles)
        print(f"Processing {total} articles...")

        # Process each article
        for i, article_data in enumerate(articles, 1):
            try:
                article = process_single_article(session, article_data, scrape_delay)

                if article:
                    # Commit immediately after each successful article
                    session.commit()
                    processed_count += 1
                else:
                    skipped_count += 1

                # Update progress counter
                print(f"\rProcessed: {i}/{total} articles ({processed_count} added, {skipped_count} skipped)", end='', flush=True)

            except Exception as e:
                logger.error(f"\nError processing article: {e}")
                session.rollback()  # Rollback failed transaction
                error_count += 1
                print(f"\rProcessed: {i}/{total} articles ({processed_count} added, {skipped_count} skipped)", end='', flush=True)
                continue

        print()  # New line after progress counter
        # Commit all changes
        session.commit()

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        session.rollback()
        raise

    finally:
        if close_session:
            session.close()

    # Summary
    print(f"\nSummary: {processed_count} added, {skipped_count} skipped, {error_count} errors")

    return processed_count


def main():
    """Run the processing pipeline."""
    print("Starting Article Processing Pipeline\n")

    # Process articles
    count = process_articles()

    print(f"\nPipeline complete: {count} articles added to database")


if __name__ == "__main__":
    main()
