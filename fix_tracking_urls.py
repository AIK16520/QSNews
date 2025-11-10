"""
Fix malformed tracking URLs by following redirects to get real destinations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_session, Newsletter
import requests
import logging
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def follow_redirect(url: str, timeout: int = 10) -> str:
    """
    Follow URL redirects to get the final destination.

    Args:
        url: The tracking URL
        timeout: Request timeout in seconds

    Returns:
        Final destination URL or original URL if redirect fails
    """
    try:
        # Try HEAD request first (faster)
        response = requests.head(url, allow_redirects=True, timeout=timeout,
                                headers={'User-Agent': 'Mozilla/5.0'})
        final_url = response.url

        # If HEAD didn't work, try GET
        if final_url == url and response.status_code >= 400:
            response = requests.get(url, allow_redirects=True, timeout=timeout,
                                   headers={'User-Agent': 'Mozilla/5.0'},
                                   stream=True)  # Stream to avoid downloading full content
            final_url = response.url
            response.close()  # Close connection immediately

        # Only return if we got a different URL
        if final_url != url:
            logger.info(f"  Resolved: {url[:80]}...")
            logger.info(f"       -> {final_url[:80]}...")
            return final_url
        else:
            return url

    except requests.RequestException as e:
        logger.debug(f"Failed to resolve {url[:80]}...: {e}")
        return url
    except Exception as e:
        logger.debug(f"Error resolving {url[:80]}...: {e}")
        return url


def is_tracking_url(url: str) -> bool:
    """Check if URL is a known tracking link."""
    tracking_domains = [
        'link.mail.beehiiv.com',
        'link.gettheelevator.com',
        'marketing.statnews.com',
        'click.convertkit-mail',
        'email.mg.',
        'elink',  # Catches elinkaf6.insidr.ai, etc.
        'substack.com/redirect',
        'insidr.ai',  # Insidr tracking
        'beehiiv.com/p/',  # Beehiiv public links
        'mandrillapp.com',
        'list-manage.com',
        'links.ml.',
        'go.redirectingat.com',
        'link.mail.',
    ]

    # Also check if URL is extremely long (>400 chars = likely tracking)
    if len(url) > 400:
        return True

    for domain in tracking_domains:
        if domain in url:
            return True

    return False


def fix_newsletter_links(dry_run: bool = True, max_newsletters: int = None):
    """
    Fix tracking URLs in newsletters by following redirects.

    Args:
        dry_run: If True, only show what would be fixed
        max_newsletters: Maximum number of newsletters to process (None for all)
    """
    session = get_session()

    try:
        # Get all newsletters
        query = session.query(Newsletter)
        if max_newsletters:
            newsletters = query.limit(max_newsletters).all()
        else:
            newsletters = query.all()

        logger.info(f"Processing {len(newsletters)} newsletters...")

        fixed_count = 0
        newsletter_count = 0

        for nl in newsletters:
            links = nl.extracted_links or []
            if not links:
                continue

            has_tracking = False
            fixed_links = []

            for link in links:
                url = link.get('url', '')

                if is_tracking_url(url):
                    has_tracking = True
                    # Follow redirect to get real URL
                    real_url = follow_redirect(url)

                    # Update link with real URL
                    fixed_link = link.copy()
                    fixed_link['url'] = real_url
                    fixed_link['original_tracking_url'] = url  # Keep original for reference
                    fixed_links.append(fixed_link)

                    if real_url != url:
                        logger.info(f"  Fixed: {link['title'][:50]}")
                        logger.info(f"    From: {url[:80]}...")
                        logger.info(f"    To:   {real_url[:80]}...")
                        fixed_count += 1
                else:
                    fixed_links.append(link)

            if has_tracking:
                newsletter_count += 1

                if not dry_run:
                    nl.extracted_links = fixed_links
                    session.add(nl)
                    logger.info(f"✓ Updated: {nl.source} - {nl.title[:60]}")
                else:
                    logger.info(f"→ Would update: {nl.source} - {nl.title[:60]}")

        if not dry_run and newsletter_count > 0:
            session.commit()
            logger.info(f"\n✓ Committed changes to database")

        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Newsletters processed: {len(newsletters)}")
        logger.info(f"Newsletters with tracking links: {newsletter_count}")
        logger.info(f"Links fixed: {fixed_count}")

        if dry_run:
            logger.info(f"\n⚠ DRY RUN - No changes saved. Run with --commit to save changes.")

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
        description='Fix tracking URLs by following redirects'
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Actually save changes (default is dry-run)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of newsletters to process (for testing)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("FIXING TRACKING URLs")
    logger.info("="*80)
    logger.info(f"Mode: {'COMMIT' if args.commit else 'DRY RUN'}")
    if args.limit:
        logger.info(f"Limit: {args.limit} newsletters")
    logger.info("="*80 + "\n")

    fix_newsletter_links(dry_run=not args.commit, max_newsletters=args.limit)

    logger.info("\n" + "="*80)
    logger.info("COMPLETE")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
