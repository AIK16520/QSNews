"""
Newsletter Archive Scraper
Scrapes historic newsletters from public archives (Beehiiv, Substack, web archives).
"""

import logging
import requests
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
import feedparser

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import improved link extractor
from src.utils.link_extractor import extract_and_explain_links

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Newsletter archive configurations
NEWSLETTER_ARCHIVES = {
    'The Rundown': {
        'type': 'web',
        'archive_url': 'https://www.therundown.ai/archive',
        'scraper': 'rundown'
    },
    "Ben's Bites": {
        'type': 'beehiiv_rss',
        'rss_url': 'https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml',
        'scraper': 'beehiiv_rss'
    },
    'TLDR AI': {
        'type': 'web',
        'archive_url': 'https://tldr.tech/ai/archives',
        'scraper': 'tldr'
    },
    'AI Breakfast': {
        'type': 'beehiiv',
        'archive_url': 'https://aibreakfast.beehiiv.com/archive',
        'scraper': 'beehiiv_web'
    },
    'Future Tools': {
        'type': 'beehiiv',
        'archive_url': 'https://futuretools.beehiiv.com/archive',
        'scraper': 'beehiiv_web'
    },
    'Last Week in AI': {
        'type': 'rss',
        'rss_url': 'https://lastweekin.ai/feed',
        'scraper': 'wordpress_rss'
    },
    'TheSequence': {
        'type': 'substack',
        'rss_url': 'https://thesequence.substack.com/feed',
        'archive_url': 'https://thesequence.substack.com/archive',
        'scraper': 'substack'
    },
    'One Useful Thing': {
        'type': 'substack',
        'rss_url': 'https://www.oneusefulthing.org/feed',
        'scraper': 'wordpress_rss'
    },
    'Import AI': {
        'type': 'substack',
        'rss_url': 'https://importai.substack.com/feed',
        'archive_url': 'https://importai.substack.com/archive',
        'scraper': 'substack'
    },
    'AIIN Healthcare': {
        'type': 'web',
        'archive_url': 'https://aiin.healthcare/newsletters',
        'scraper': 'aiin_healthcare'
    },
    'Axios AI': {
        'type': 'web',
        'archive_url': 'https://www.axios.com/technology/automation-and-ai',
        'scraper': 'axios'
    },
}


def scrape_beehiiv_rss(rss_url: str, days_back: int = 30) -> List[Dict]:
    """Scrape Beehiiv newsletter via RSS feed."""
    newsletters = []

    try:
        logger.info(f"Fetching Beehiiv RSS: {rss_url}")
        feed = feedparser.parse(rss_url)

        cutoff_date = datetime.now() - timedelta(days=days_back)

        for entry in feed.entries:
            try:
                # Parse publication date
                pub_date = datetime(*entry.published_parsed[:6])

                if pub_date < cutoff_date:
                    continue

                # Extract content
                title = entry.title
                link = entry.link
                summary = entry.get('summary', '')

                # Get full content if available
                content = entry.get('content', [{}])[0].get('value', summary)

                # Extract links with improved extraction
                links = extract_and_explain_links(content, source="Ben's Bites")

                # Extract plain text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                plain_text = soup.get_text(separator='\n', strip=True)

                newsletters.append({
                    'title': title,
                    'email_subject': title,
                    'published_date': pub_date,
                    'received_date': pub_date,
                    'html_content': content,
                    'plain_text': plain_text,
                    'extracted_links': links,
                    'from_email': feed.feed.get('link', ''),
                    'archive_url': link
                })

                logger.info(f"  Scraped: {title[:60]} ({pub_date.strftime('%Y-%m-%d')})")

            except Exception as e:
                logger.warning(f"Error parsing RSS entry: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping Beehiiv RSS: {e}")

    return newsletters


def scrape_substack_rss(rss_url: str, days_back: int = 30) -> List[Dict]:
    """Scrape Substack newsletter via RSS feed."""
    newsletters = []

    try:
        logger.info(f"Fetching Substack RSS: {rss_url}")
        feed = feedparser.parse(rss_url)

        cutoff_date = datetime.now() - timedelta(days=days_back)

        for entry in feed.entries:
            try:
                # Parse publication date
                pub_date = datetime(*entry.published_parsed[:6])

                if pub_date < cutoff_date:
                    continue

                title = entry.title
                link = entry.link
                summary = entry.get('summary', '')

                # Get full content
                content = entry.get('content', [{}])[0].get('value', summary)

                # Determine source from feed
                feed_link = feed.feed.get('link', '')
                source_name = 'Substack'
                if 'thesequence' in feed_link:
                    source_name = 'TheSequence'
                elif 'oneusefulthing' in feed_link:
                    source_name = 'One Useful Thing'
                elif 'importai' in feed_link:
                    source_name = 'Import AI'

                # Extract links with improved extraction
                links = extract_and_explain_links(content, source=source_name)

                # Extract plain text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                plain_text = soup.get_text(separator='\n', strip=True)

                newsletters.append({
                    'title': title,
                    'email_subject': title,
                    'published_date': pub_date,
                    'received_date': pub_date,
                    'html_content': content,
                    'plain_text': plain_text,
                    'extracted_links': links,
                    'from_email': feed.feed.get('link', ''),
                    'archive_url': link
                })

                logger.info(f"  Scraped: {title[:60]} ({pub_date.strftime('%Y-%m-%d')})")

            except Exception as e:
                logger.warning(f"Error parsing Substack entry: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping Substack RSS: {e}")

    return newsletters


def scrape_wordpress_rss(rss_url: str, days_back: int = 30) -> List[Dict]:
    """Scrape WordPress-based newsletter via RSS."""
    return scrape_substack_rss(rss_url, days_back)  # Same logic


def scrape_newsletter_archive(
    source_name: str,
    days_back: int = 30
) -> List[Dict]:
    """
    Scrape historic newsletters from a specific source.

    Args:
        source_name: Newsletter name (must be in NEWSLETTER_ARCHIVES)
        days_back: How many days back to scrape

    Returns:
        List of newsletter dictionaries
    """
    if source_name not in NEWSLETTER_ARCHIVES:
        logger.warning(f"No archive configuration for: {source_name}")
        return []

    config = NEWSLETTER_ARCHIVES[source_name]
    scraper_type = config.get('scraper')

    logger.info(f"Scraping {source_name} archive (type: {scraper_type})")

    newsletters = []

    try:
        if scraper_type == 'beehiiv_rss':
            newsletters = scrape_beehiiv_rss(config['rss_url'], days_back)

        elif scraper_type == 'substack':
            newsletters = scrape_substack_rss(config['rss_url'], days_back)

        elif scraper_type == 'wordpress_rss':
            newsletters = scrape_wordpress_rss(config['rss_url'], days_back)

        elif scraper_type == 'beehiiv_web':
            logger.warning(f"Web scraping for {source_name} not yet implemented (use email instead)")

        elif scraper_type == 'rundown':
            logger.warning(f"The Rundown scraping not yet implemented (use email instead)")

        elif scraper_type == 'tldr':
            logger.warning(f"TLDR scraping not yet implemented (use email instead)")

        elif scraper_type == 'aiin_healthcare':
            logger.warning(f"AIIN Healthcare scraping not yet implemented (use email instead)")

        elif scraper_type == 'axios':
            logger.warning(f"Axios scraping not yet implemented (use email instead)")

        else:
            logger.warning(f"Unknown scraper type: {scraper_type}")

        # Add source to each newsletter
        for newsletter in newsletters:
            newsletter['source'] = source_name

    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")

    logger.info(f"Scraped {len(newsletters)} newsletters from {source_name}")
    return newsletters


def scrape_all_archives(days_back: int = 30) -> Dict[str, List[Dict]]:
    """
    Scrape all configured newsletter archives.

    Returns:
        Dictionary mapping source name to list of newsletters
    """
    all_newsletters = {}

    for source_name in NEWSLETTER_ARCHIVES.keys():
        try:
            newsletters = scrape_newsletter_archive(source_name, days_back)
            if newsletters:
                all_newsletters[source_name] = newsletters

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            continue

    total = sum(len(nls) for nls in all_newsletters.values())
    logger.info(f"Total scraped: {total} newsletters from {len(all_newsletters)} sources")

    return all_newsletters


if __name__ == "__main__":
    # Test the archive scraper
    print("\n" + "="*80)
    print("TESTING NEWSLETTER ARCHIVE SCRAPER")
    print("="*80 + "\n")

    # Test with Ben's Bites (has RSS)
    print("Testing Ben's Bites archive scraping...")
    newsletters = scrape_newsletter_archive("Ben's Bites", days_back=7)

    if newsletters:
        print(f"\nSuccessfully scraped {len(newsletters)} newsletters from Ben's Bites:")
        for nl in newsletters[:3]:
            print(f"  - {nl['title']} ({nl['published_date'].strftime('%Y-%m-%d')})")
            print(f"    Links: {len(nl['extracted_links'])}")
    else:
        print("No newsletters found (might need to wait for RSS or check configuration)")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")
