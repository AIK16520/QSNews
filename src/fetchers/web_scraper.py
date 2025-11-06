"""
Web Scraper Module
Hybrid scraper using newspaper4k (primary) and trafilatura (fallback).
Extracts full article content from URLs.
Also provides article discovery for websites without RSS feeds.
"""

import logging
import time
from typing import Optional, List, Dict
from datetime import datetime

from newspaper import Article, Config as NewspaperConfig, Source
import trafilatura
import requests
from bs4 import BeautifulSoup

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure failure logging
failure_logger = logging.getLogger('scraping_failures')
failure_handler = logging.FileHandler('data/scraping_failures.log')
failure_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
failure_logger.addHandler(failure_handler)
failure_logger.setLevel(logging.WARNING)


class HybridScraper:
    """
    Hybrid web scraper using newspaper4k as primary and trafilatura as fallback.
    """

    def __init__(self):
        """Initialize the hybrid scraper with configurations."""
        # Configure newspaper4k
        self.newspaper_config = NewspaperConfig()
        self.newspaper_config.browser_user_agent = config.USER_AGENT
        self.newspaper_config.request_timeout = config.SCRAPING_TIMEOUT
        self.newspaper_config.fetch_images = False
        self.newspaper_config.memoize_articles = False
        self.newspaper_config.language = 'en'
        self.newspaper_config.number_threads = 1  # Single thread per request

        self.min_length = config.MIN_ARTICLE_LENGTH
        self.timeout = config.SCRAPING_TIMEOUT

    def _newspaper_scrape(self, url: str) -> Optional[str]:
        """
        Scrape article using newspaper4k.

        Args:
            url: Article URL

        Returns:
            Article text or None if failed
        """
        try:
            article = Article(url, config=self.newspaper_config)
            article.download()
            article.parse()

            # Get the text
            text = article.text

            if text and len(text) >= self.min_length:
                logger.debug(f"newspaper4k success: {url} ({len(text)} chars)")
                return text.strip()
            else:
                logger.debug(f"newspaper4k returned short content: {url} ({len(text) if text else 0} chars)")
                return None

        except Exception as e:
            logger.debug(f"newspaper4k failed for {url}: {e}")
            return None

    def _trafilatura_scrape(self, url: str) -> Optional[str]:
        """
        Scrape article using trafilatura (fallback).

        Args:
            url: Article URL

        Returns:
            Article text or None if failed
        """
        try:
            # Download with requests first
            headers = {'User-Agent': config.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Extract with trafilatura
            text = trafilatura.extract(
                response.content,
                include_comments=False,
                include_tables=False,
                no_fallback=False
            )

            if text and len(text) >= self.min_length:
                logger.debug(f"trafilatura success: {url} ({len(text)} chars)")
                return text.strip()
            else:
                logger.debug(f"trafilatura returned short content: {url} ({len(text) if text else 0} chars)")
                return None

        except Exception as e:
            logger.debug(f"trafilatura failed for {url}: {e}")
            return None

    def scrape_article_content(self, url: str) -> Optional[str]:
        """
        Scrape article content using hybrid approach.
        Tries newspaper4k first, then trafilatura.

        Args:
            url: Article URL

        Returns:
            Article text or None if both methods fail
        """
        logger.info(f"Scraping: {url}")

        # Try newspaper4k first
        content = self._newspaper_scrape(url)
        if content:
            logger.info(f" Scraped successfully with newspaper4k ({len(content)} chars)")
            return content

        # Fallback to trafilatura
        logger.debug(f"Trying trafilatura fallback for {url}")
        content = self._trafilatura_scrape(url)
        if content:
            logger.info(f" Scraped successfully with trafilatura ({len(content)} chars)")
            return content

        # Both failed
        logger.warning(f" Failed to scrape {url} (both methods)")
        failure_logger.warning(f"{url} - Both methods failed")
        return None


# Global scraper instance
_scraper = None


def get_scraper() -> HybridScraper:
    """Get or create global scraper instance."""
    global _scraper
    if _scraper is None:
        _scraper = HybridScraper()
    return _scraper


def scrape_article_content(url: str) -> Optional[str]:
    """
    Scrape article content from URL.
    Convenience function that uses the global scraper instance.

    Args:
        url: Article URL

    Returns:
        Article text or None if scraping failed
    """
    scraper = get_scraper()
    return scraper.scrape_article_content(url)


def scrape_multiple_articles(urls: list, delay: float = 2.0) -> dict:
    """
    Scrape multiple articles with rate limiting.

    Args:
        urls: List of article URLs
        delay: Delay between requests in seconds

    Returns:
        Dictionary mapping URL to content (or None if failed)
    """
    results = {}
    scraper = get_scraper()

    for i, url in enumerate(urls, 1):
        logger.info(f"Scraping article {i}/{len(urls)}")

        content = scraper.scrape_article_content(url)
        results[url] = content

        # Rate limiting (except for last article)
        if i < len(urls):
            time.sleep(delay)

    # Summary
    success_count = sum(1 for v in results.values() if v is not None)
    logger.info(f"Scraping complete: {success_count}/{len(urls)} successful")

    return results


def discover_strictlyvc_articles(max_articles: int = 20) -> List[Dict]:
    """
    Discover articles from StrictlyVC newsletter website.
    Returns articles in the same format as RSS fetcher.

    Args:
        max_articles: Maximum number of articles to discover

    Returns:
        List of article dictionaries with keys: url, title, source, published_date, rss_summary
    """
    articles = []
    source_name = "StrictlyVC"
    base_url = "https://newsletter.strictlyvc.com"

    try:
        # Configure newspaper
        newspaper_config = NewspaperConfig()
        newspaper_config.browser_user_agent = config.USER_AGENT
        newspaper_config.request_timeout = config.SCRAPING_TIMEOUT
        newspaper_config.thread_timeout_seconds = config.SCRAPING_TIMEOUT + 5  # Must be >= request_timeout
        newspaper_config.memoize_articles = False

        # Build source (discover articles)

        # Suppress FutureWarning from newspaper library
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            source = Source(base_url, config=newspaper_config)
            source.build()

        # Process discovered articles
        article_urls = list(source.article_urls())[:max_articles]

        for url in article_urls:
            try:

                # Download and parse article for metadata
                article = Article(url, config=newspaper_config)
                article.download()
                article.parse()

                # Extract metadata
                title = article.title or "No Title"
                published_date = article.publish_date

                # Create article dictionary (same format as RSS fetcher)
                article_dict = {
                    'url': url,
                    'title': title,
                    'source': source_name,
                    'published_date': published_date.isoformat() if published_date else None,
                    'rss_summary': article.meta_description or None
                }

                articles.append(article_dict)

                # Small delay to be respectful
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error fetching metadata for {url}: {e}")
                # Still add the article with minimal info
                articles.append({
                    'url': url,
                    'title': url.split('/')[-1].replace('-', ' ').title(),
                    'source': source_name,
                    'published_date': None,
                    'rss_summary': None
                })
                continue

    except Exception as e:
        logger.error(f"Error discovering articles from {source_name}: {e}")

        # Fallback: Try manual scraping
        logger.info("Attempting fallback manual discovery...")
        articles = discover_strictlyvc_fallback(max_articles)

    logger.info(f"Total articles discovered from {source_name}: {len(articles)}")
    return articles


def discover_strictlyvc_fallback(max_articles: int = 20) -> List[Dict]:
    """
    Fallback method to discover StrictlyVC articles using BeautifulSoup.

    Args:
        max_articles: Maximum number of articles to discover

    Returns:
        List of article dictionaries
    """
    articles = []
    source_name = "StrictlyVC"
    base_url = "https://newsletter.strictlyvc.com"

    try:
        logger.info("Using fallback discovery for StrictlyVC")

        response = requests.get(
            base_url,
            headers={'User-Agent': config.USER_AGENT},
            timeout=config.SCRAPING_TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to find article links (Beehiiv newsletters typically use /p/ for posts)
        article_links = []

        # Try multiple selector patterns
        for selector in ['a[href*="/p/"]', 'a.post-link', 'article a', '.post a', 'h2 a', 'h3 a']:
            links = soup.select(selector)
            if links:
                article_links.extend(links)

        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in article_links:
            url = link.get('href', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_links.append(link)

        logger.info(f"Found {len(unique_links)} unique article links")

        # Process links
        for link in unique_links[:max_articles]:
            try:
                url = link['href']

                # Make absolute URL
                if url.startswith('/'):
                    url = f"{base_url}{url}"
                elif not url.startswith('http'):
                    continue  # Skip invalid URLs

                # Get title from link text
                title = link.get_text(strip=True) or link.get('title', 'No Title')

                article_dict = {
                    'url': url,
                    'title': title,
                    'source': source_name,
                    'published_date': None,  # Will be extracted during processing
                    'rss_summary': None
                }

                articles.append(article_dict)
                logger.info(f"Found: {title}")

            except Exception as e:
                logger.error(f"Error processing link: {e}")
                continue

    except Exception as e:
        logger.error(f"Fallback discovery failed: {e}")

    return articles


def discover_anthropic_articles(max_articles: int = 15) -> List[Dict]:
    """
    Discover articles from Anthropic news page.
    Returns articles in the same format as RSS fetcher.

    Args:
        max_articles: Maximum number of articles to discover

    Returns:
        List of article dictionaries with keys: url, title, source, published_date, rss_summary
    """
    articles = []
    source_name = "Anthropic"
    base_url = "https://www.anthropic.com"
    news_url = f"{base_url}/news"

    try:
        response = requests.get(
            news_url,
            headers={'User-Agent': config.USER_AGENT},
            timeout=config.SCRAPING_TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for article links - Anthropic uses /news/[slug] pattern
        article_links = []

        # Try multiple selector patterns to find article links
        for selector in ['a[href*="/news/"]', 'article a', '.post a', 'h2 a', 'h3 a', 'div[class*="card"] a', 'div[class*="post"] a']:
            links = soup.select(selector)
            if links:
                article_links.extend(links)

        # Remove duplicates and filter valid article URLs
        seen_urls = set()
        unique_links = []
        for link in article_links:
            url = link.get('href', '')

            # Make absolute URL
            if url.startswith('/'):
                url = f"{base_url}{url}"

            # Only include /news/ articles and skip the main news page itself
            if url and url not in seen_urls and '/news/' in url and url != news_url and not url.endswith('/news'):
                seen_urls.add(url)
                unique_links.append({'url': url, 'element': link})

        # Process articles
        for item in unique_links[:max_articles]:
            try:
                url = item['url']
                link_element = item['element']

                # Try to get title from link text or nearby heading
                title = link_element.get_text(strip=True)

                # If title is empty or very short, try to find nearby heading
                if not title or len(title) < 5:
                    parent = link_element.parent
                    if parent:
                        heading = parent.find(['h1', 'h2', 'h3', 'h4'])
                        if heading:
                            title = heading.get_text(strip=True)

                # Fallback: use URL slug as title
                if not title or len(title) < 5:
                    title = url.split('/')[-1].replace('-', ' ').title()

                article_dict = {
                    'url': url,
                    'title': title,
                    'source': source_name,
                    'published_date': None,  # Will be extracted during content scraping
                    'rss_summary': None
                }

                articles.append(article_dict)

            except Exception as e:
                logger.error(f"Error processing link: {e}")
                continue

        # If we didn't find enough articles, try newspaper4k as fallback
        if len(articles) < 3:
            try:
                newspaper_config = NewspaperConfig()
                newspaper_config.browser_user_agent = config.USER_AGENT
                newspaper_config.request_timeout = config.SCRAPING_TIMEOUT
                newspaper_config.thread_timeout_seconds = config.SCRAPING_TIMEOUT + 5
                newspaper_config.memoize_articles = False

                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    source = Source(news_url, config=newspaper_config)
                    source.build()

                article_urls = list(source.article_urls())[:max_articles]

                for url in article_urls:
                    if url not in seen_urls:
                        articles.append({
                            'url': url,
                            'title': url.split('/')[-1].replace('-', ' ').title(),
                            'source': source_name,
                            'published_date': None,
                            'rss_summary': None
                        })

            except Exception as e:
                logger.error(f"Newspaper4k fallback failed for Anthropic: {e}")

    except Exception as e:
        logger.error(f"Error discovering articles from {source_name}: {e}")

    return articles


def discover_all_web_sources() -> List[Dict]:
    """
    Discover articles from all custom (non-RSS) web sources.

    Returns:
        List of article dictionaries in RSS fetcher format
    """
    all_articles = []

    # Add StrictlyVC
    strictlyvc_articles = discover_strictlyvc_articles()
    all_articles.extend(strictlyvc_articles)

    # Add Anthropic
    anthropic_articles = discover_anthropic_articles()
    all_articles.extend(anthropic_articles)

    # Add more custom sources here in the future

    return all_articles


def main():
    """Test the web scraper with sample URLs."""
    print("Testing Web Scraper\n")

    # Test URLs (replace with actual URLs for testing)
    test_urls = [
        "https://techcrunch.com/2024/01/15/openai-announces-new-features/",
        "https://www.theverge.com/2024/1/10/ai-news-article/",
        "https://venturebeat.com/ai/latest-ai-developments/"
    ]

    print(f"Testing with {len(test_urls)} URLs...\n")

    # Scrape articles
    results = scrape_multiple_articles(test_urls)

    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    for url, content in results.items():
        print(f"\nURL: {url}")
        if content:
            preview = content[:200].replace('\n', ' ')
            print(f" Success ({len(content)} chars)")
            print(f"  Preview: {preview}...")
        else:
            print(" Failed")

    # Statistics
    success_count = sum(1 for v in results.values() if v is not None)
    print(f"\n" + "="*80)
    print(f"Success Rate: {success_count}/{len(test_urls)} ({success_count/len(test_urls)*100:.1f}%)")
    print("="*80)


if __name__ == "__main__":
    main()
