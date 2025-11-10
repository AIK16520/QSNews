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
    'Sequoia Capital': {
        'type': 'rss',
        'rss_url': 'https://www.sequoiacap.com/feed/',
        'scraper': 'sequoia_rss'
    },
    'Chief AI Office': {
        'type': 'beehiiv_web',
        'archive_url': 'https://www.chiefaioffice.xyz/',
        'scraper': 'chief_ai_office'
    },
    'Micro SaaS Idea': {
        'type': 'substack',
        'rss_url': 'https://microsaasidea.substack.com/feed',
        'archive_url': 'https://microsaasidea.substack.com/archive',
        'scraper': 'microsaas_custom'
    },
}


def scrape_beehiiv_rss(rss_url: str, days_back: int = 30, source_name: str = 'Beehiiv') -> List[Dict]:
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


def scrape_techcrunch_rss(rss_url: str, days_back: int = 30) -> List[Dict]:
    """Scrape TechCrunch articles via RSS feed."""
    newsletters = []

    try:
        logger.info(f"Fetching TechCrunch RSS: {rss_url}")
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

                # Determine specific newsletter type from categories/tags
                source_name = 'TechCrunch'
                tags = [tag.get('term', '').lower() for tag in entry.get('tags', [])]

                if 'startups' in tags or 'startup' in title.lower():
                    source_name = 'TechCrunch Startups Weekly'
                elif 'daily' in title.lower():
                    source_name = 'TechCrunch Daily'

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
                    'from_email': 'techcrunch.com',
                    'archive_url': link
                })

                logger.info(f"  Scraped: {title[:60]} ({pub_date.strftime('%Y-%m-%d')})")

            except Exception as e:
                logger.warning(f"Error parsing TechCrunch RSS entry: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping TechCrunch RSS: {e}")

    return newsletters


def scrape_sequoia_rss(rss_url: str, days_back: int = 30) -> List[Dict]:
    """Scrape Sequoia Capital news via RSS feed."""
    newsletters = []

    try:
        logger.info(f"Fetching Sequoia Capital RSS: {rss_url}")
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

                # Extract links with improved extraction
                links = extract_and_explain_links(content, source='Sequoia Capital')

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
                    'from_email': 'sequoiacap.com',
                    'archive_url': link
                })

                logger.info(f"  Scraped: {title[:60]} ({pub_date.strftime('%Y-%m-%d')})")

            except Exception as e:
                logger.warning(f"Error parsing Sequoia RSS entry: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping Sequoia RSS: {e}")

    return newsletters


def scrape_microsaas_custom(rss_url: str, days_back: int = 30) -> List[Dict]:
    """
    Scrape Micro SaaS Idea newsletter with custom link extraction.
    Only extracts links from 'Recent Micro SaaS News in 2 minutes' section.
    """
    newsletters = []

    try:
        logger.info(f"Fetching Micro SaaS Idea RSS: {rss_url}")
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

                # Extract ONLY the "Recent Micro SaaS News" section
                filtered_content = extract_microsaas_news_section(content)

                # Extract links ONLY from filtered content
                links = extract_and_explain_links(filtered_content, source='Micro SaaS Idea')

                # Extract plain text from filtered HTML
                soup = BeautifulSoup(filtered_content, 'html.parser')
                plain_text = soup.get_text(separator='\n', strip=True)

                newsletters.append({
                    'title': title,
                    'email_subject': title,
                    'published_date': pub_date,
                    'received_date': pub_date,
                    'html_content': filtered_content,  # Filtered content only
                    'plain_text': plain_text,
                    'extracted_links': links,
                    'from_email': 'microsaasidea.substack.com',
                    'archive_url': link
                })

                logger.info(f"  Scraped: {title[:60]} ({pub_date.strftime('%Y-%m-%d')}) - {len(links)} links from news section")

            except Exception as e:
                logger.warning(f"Error parsing Micro SaaS Idea entry: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping Micro SaaS Idea RSS: {e}")

    return newsletters


def extract_microsaas_news_section(html_content: str) -> str:
    """
    Extract ONLY the 'Recent Micro SaaS News in 2 minutes' section.
    Stops at 'Get Access to 1000+ ideas & Community'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the start marker
    start_markers = [
        '🎉 ✨ Recent Micro SaaS News in 2 minutes',
        'Recent Micro SaaS News in 2 minutes',
        'Recent Micro SaaS News'
    ]

    # Find the end markers
    end_markers = [
        'Get Access to 1000+ ideas & Community',
        'Unlock 500+ Micro SaaS News Updates',
        'Deep-dive',
        '🤿🤿 Deep-dive',
        'Micro SaaS niches'
    ]

    content_text = soup.get_text()

    # Find start position
    start_pos = -1
    for marker in start_markers:
        if marker in content_text:
            start_pos = content_text.find(marker)
            break

    if start_pos == -1:
        # If we can't find the marker, return empty to avoid including unwanted content
        logger.warning("Could not find 'Recent Micro SaaS News' section start marker")
        return ""

    # Find end position
    end_pos = len(content_text)
    for marker in end_markers:
        pos = content_text.find(marker, start_pos)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    # Extract the section text
    section_text = content_text[start_pos:end_pos]

    # Now extract HTML elements that contain this text
    # We'll rebuild HTML with only the relevant content
    filtered_html_parts = []

    for element in soup.find_all(['p', 'div', 'span', 'a', 'li', 'ul']):
        element_text = element.get_text(strip=True)

        # Check if this element's text appears in our section
        if element_text and element_text in section_text:
            # Check it's not in the "deep-dive" or promotional sections
            is_excluded = False
            for end_marker in end_markers:
                if end_marker.lower() in element_text.lower():
                    is_excluded = True
                    break

            if not is_excluded:
                filtered_html_parts.append(str(element))

    filtered_html = '\n'.join(filtered_html_parts)

    logger.info(f"  Extracted news section: {len(filtered_html)} chars")
    return filtered_html if filtered_html else html_content  # Fallback to full content if filtering fails


def scrape_chief_ai_office(archive_url: str, limit: int = 20) -> List[Dict]:
    """Scrape Chief AI Office newsletter archive from web page."""
    newsletters = []

    try:
        logger.info(f"Fetching Chief AI Office archive: {archive_url}")

        # Fetch the main archive page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(archive_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all newsletter links (they follow pattern /p/{slug})
        newsletter_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/p/'):
                full_url = f"https://www.chiefaioffice.xyz{href}"
                if full_url not in newsletter_links:
                    newsletter_links.append(full_url)
                    if len(newsletter_links) >= limit:
                        break

        logger.info(f"Found {len(newsletter_links)} newsletter links")

        # Scrape each newsletter
        for i, newsletter_url in enumerate(newsletter_links, 1):
            try:
                logger.info(f"  [{i}/{len(newsletter_links)}] Fetching: {newsletter_url}")

                time.sleep(1)  # Rate limiting

                resp = requests.get(newsletter_url, headers=headers, timeout=30)
                resp.raise_for_status()

                nl_soup = BeautifulSoup(resp.text, 'html.parser')

                # Extract title
                title_tag = nl_soup.find('h1')
                title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

                # Extract date - look for time or date elements
                pub_date = datetime.now()  # Default to now if we can't find date
                time_tag = nl_soup.find('time')
                if time_tag and time_tag.get('datetime'):
                    try:
                        from dateutil import parser as date_parser
                        pub_date = date_parser.parse(time_tag['datetime'])
                    except:
                        pass

                # Get main content
                content_div = nl_soup.find('div', class_='post-content') or nl_soup.find('article')
                if content_div:
                    html_content = str(content_div)
                    plain_text = content_div.get_text(separator='\n', strip=True)
                else:
                    html_content = resp.text
                    plain_text = nl_soup.get_text(separator='\n', strip=True)

                # Extract links
                links = extract_and_explain_links(html_content, source='Chief AI Office')

                newsletters.append({
                    'title': title,
                    'email_subject': title,
                    'published_date': pub_date,
                    'received_date': pub_date,
                    'html_content': html_content,
                    'plain_text': plain_text,
                    'extracted_links': links,
                    'from_email': 'chiefaioffice.xyz',
                    'archive_url': newsletter_url
                })

                logger.info(f"    Scraped: {title[:60]}")

            except Exception as e:
                logger.warning(f"    Error scraping newsletter: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping Chief AI Office archive: {e}")

    return newsletters


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
            newsletters = scrape_beehiiv_rss(config['rss_url'], days_back, source_name)

        elif scraper_type == 'substack':
            newsletters = scrape_substack_rss(config['rss_url'], days_back)

        elif scraper_type == 'wordpress_rss':
            newsletters = scrape_wordpress_rss(config['rss_url'], days_back)

        elif scraper_type == 'techcrunch_rss':
            newsletters = scrape_techcrunch_rss(config['rss_url'], days_back)

        elif scraper_type == 'sequoia_rss':
            newsletters = scrape_sequoia_rss(config['rss_url'], days_back)

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

        elif scraper_type == 'chief_ai_office':
            newsletters = scrape_chief_ai_office(config['archive_url'], limit=20)

        elif scraper_type == 'microsaas_custom':
            newsletters = scrape_microsaas_custom(config['rss_url'], days_back)

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
