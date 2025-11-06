"""
Test script for Anthropic news scraper.
Run this to test the Anthropic article discovery functionality.
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fetchers.web_scraper import discover_anthropic_articles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test the Anthropic scraper."""
    print("\n" + "="*80)
    print("TESTING ANTHROPIC NEWS SCRAPER")
    print("="*80 + "\n")

    start_time = datetime.now()

    try:
        # Fetch Anthropic articles
        articles = discover_anthropic_articles(max_articles=15)

        # Display results
        print(f"\n{'='*80}")
        print(f"RESULTS: Found {len(articles)} articles from Anthropic")
        print(f"{'='*80}\n")

        if articles:
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article['title']}")
                print(f"   URL: {article['url']}")
                print(f"   Source: {article['source']}")
                print(f"   Published: {article.get('published_date', 'Not available')}")
                print()
        else:
            print("No articles found. Check the logs above for errors.")

    except Exception as e:
        logger.error(f"Error testing Anthropic scraper: {e}", exc_info=True)
        print(f"\nERROR: {e}")

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*80}")
    print(f"Test completed in {elapsed:.1f}s")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
