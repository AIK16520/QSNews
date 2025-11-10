"""
RSS Fetcher Module
Discovers new articles from configured RSS feeds.
"""

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dateutil import parser as date_parser

import feedparser

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """
    Parse date string to datetime object.
    Handles various RSS date formats.
    """
    if not date_string:
        return None

    try:
        # Try using dateutil parser (very flexible)
        return date_parser.parse(date_string)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None


def fetch_rss_feed(source_name: str, rss_url: str, max_articles: int = 20) -> List[Dict]:
    """
    Fetch articles from a single RSS feed.

    Args:
        source_name: Name of the source (e.g., "TechCrunch AI")
        rss_url: URL of the RSS feed
        max_articles: Maximum number of articles to fetch

    Returns:
        List of article dictionaries
    """
    articles = []

    try:
        # Parse the RSS feed
        feed = feedparser.parse(rss_url)

        # Check for parsing errors
        if feed.bozo:
            logger.warning(f"RSS feed has parsing issues ({source_name}): {feed.bozo_exception}")

        # Extract articles
        entries = feed.entries[:max_articles]

        for entry in entries:
            try:
                # Extract URL (try multiple fields)
                url = entry.get('link') or entry.get('id')
                if not url:
                    logger.warning(f"No URL found for entry in {source_name}, skipping")
                    continue

                # Extract title
                title = entry.get('title', 'No Title')

                # Extract published date
                published_date = None
                if hasattr(entry, 'published'):
                    published_date = parse_date(entry.published)
                elif hasattr(entry, 'updated'):
                    published_date = parse_date(entry.updated)

                # Extract summary/description
                rss_summary = None
                if hasattr(entry, 'summary'):
                    rss_summary = entry.summary
                elif hasattr(entry, 'description'):
                    rss_summary = entry.description

                # Create article dictionary
                article = {
                    'url': url,
                    'title': title,
                    'source': source_name,
                    'published_date': published_date.isoformat() if published_date else None,
                    'rss_summary': rss_summary
                }

                articles.append(article)

            except Exception as e:
                logger.error(f"Error processing entry from {source_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error fetching RSS feed {source_name}: {e}")

    return articles


def fetch_all_rss() -> List[Dict]:
    """
    Fetch articles from all configured RSS sources.

    Returns:
        List of all article dictionaries from all sources
    """
    all_articles = []

    # Count sources (excluding StrictlyVC and Anthropic which are web-scraped)
    rss_sources = [name for name in config.RSS_SOURCES.keys() if name not in ["StrictlyVC", "Anthropic"]]
    total_sources = len(rss_sources)

    logger.info(f"Fetching from {total_sources} RSS sources...")

    for i, (source_name, rss_url) in enumerate(config.RSS_SOURCES.items(), 1):
        # Skip web-scraped sources
        if source_name in ["StrictlyVC", "Anthropic"]:
            continue

        print(f"\rFetching: {i}/{total_sources} sources, {len(all_articles)} articles found", end='', flush=True)

        articles = fetch_rss_feed(source_name, rss_url)
        all_articles.extend(articles)

    print(f"\rFetched: {total_sources}/{total_sources} RSS sources, {len(all_articles)} articles")

    # Add web-scraped sources (like StrictlyVC, Anthropic)
    try:
        from src.fetchers.web_scraper import discover_all_web_sources
        print(f"Fetching from web sources...", end='', flush=True)
        web_articles = discover_all_web_sources()
        all_articles.extend(web_articles)
        print(f"\rFetched: Web sources, {len(web_articles)} articles")
    except Exception as e:
        logger.error(f"Error fetching web sources: {e}")

    print(f"Total: {len(all_articles)} articles fetched")

    return all_articles


def save_fetched_articles(articles: List[Dict], output_file: str = 'data/temp_fetched.json'):
    """
    Save fetched articles to a temporary JSON file.

    Args:
        articles: List of article dictionaries
        output_file: Path to output JSON file
    """
    try:
        # Ensure directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(articles)} articles to {output_file}")

    except Exception as e:
        logger.error(f"Error saving articles to {output_file}: {e}")
        raise


def load_fetched_articles(input_file: str = 'data/temp_fetched.json') -> List[Dict]:
    """
    Load articles from temporary JSON file.

    Args:
        input_file: Path to input JSON file

    Returns:
        List of article dictionaries
    """
    try:
        if not os.path.exists(input_file):
            logger.warning(f"File {input_file} does not exist")
            return []

        with open(input_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        logger.info(f"Loaded {len(articles)} articles from {input_file}")
        return articles

    except Exception as e:
        logger.error(f"Error loading articles from {input_file}: {e}")
        return []


def main():
    """Main function for testing RSS fetcher."""
    print("Fetching articles from RSS feeds...\n")

    # Fetch all articles
    articles = fetch_all_rss()

    # Print summary
    print(f"\nTotal articles fetched: {len(articles)}")
    print("\nBreakdown by source:")

    sources = {}
    for article in articles:
        source = article['source']
        sources[source] = sources.get(source, 0) + 1

    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    # Save to file
    save_fetched_articles(articles)

    # Show first 3 articles as examples
    print("\nFirst 3 articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   URL: {article['url']}")
        print(f"   Published: {article['published_date']}")


if __name__ == "__main__":
    main()
