"""
Analyze newsletter link quality issues
Identifies problems with extracted links in newsletters
"""

import sqlite3
import json
from collections import Counter
from urllib.parse import urlparse, parse_qs

def analyze_link_quality():
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    # Get all newsletters with links
    cursor.execute('SELECT COUNT(*) FROM newsletters WHERE extracted_links IS NOT NULL')
    total_with_links = cursor.fetchone()[0]
    print(f'Total newsletters with links: {total_with_links}')

    cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
    rows = cursor.fetchall()

    # Analysis metrics
    bad_links = []
    duplicate_urls = Counter()
    tracking_urls = 0
    promotional_links = []
    total_links = 0

    # Bad title patterns
    BAD_PATTERNS = ['link', 'here', 'click here', 'read more', 'see more', 'learn more',
                    'ad spot', 'trending ai tools', 'view', 'subscribe', 'download']

    # Promotional patterns
    PROMO_PATTERNS = ['utm_', 'tracking', 'subscribe', 'unsubscribe', 'ad', 'sponsor']

    for row in rows:
        newsletter_id = row[0]
        links = json.loads(row[3]) if row[3] else []
        total_links += len(links)

        for link in links:
            title = link.get('title', '')
            url = link.get('url', '')

            # Check for bad titles
            if len(title) <= 10 or any(pattern in title.lower() for pattern in BAD_PATTERNS):
                bad_links.append({
                    'newsletter_id': newsletter_id,
                    'title': title,
                    'url': url[:100]
                })

            # Check for tracking URLs
            if 'utm_' in url or 'tracking' in url.lower():
                tracking_urls += 1

            # Count duplicates
            duplicate_urls[url] += 1

            # Check for promotional links
            if any(pattern in url.lower() for pattern in PROMO_PATTERNS):
                promotional_links.append({
                    'newsletter_id': newsletter_id,
                    'title': title,
                    'url': url[:100]
                })

    # Find actual duplicates (URLs that appear more than once)
    duplicates = {url: count for url, count in duplicate_urls.items() if count > 1}

    # Print results
    print(f'\n=== ANALYSIS RESULTS ===')
    print(f'Total links analyzed: {total_links}')
    print(f'Links with tracking parameters: {tracking_urls} ({tracking_urls/total_links*100:.1f}%)')
    print(f'Links with bad/uninformative titles: {len(bad_links)} ({len(bad_links)/total_links*100:.1f}%)')
    print(f'Duplicate URLs: {len(duplicates)} unique URLs appearing multiple times')
    print(f'Promotional links: {len(promotional_links)} ({len(promotional_links)/total_links*100:.1f}%)')

    print(f'\n=== SAMPLE BAD LINK TITLES ===')
    for item in bad_links[:20]:
        print(f'  Newsletter {item["newsletter_id"]}: "{item["title"]}"')
        print(f'    URL: {item["url"]}')

    print(f'\n=== MOST DUPLICATED URLS ===')
    for url, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'  {count}x: {url[:100]}')

    print(f'\n=== SAMPLE PROMOTIONAL LINKS ===')
    for item in promotional_links[:15]:
        print(f'  Newsletter {item["newsletter_id"]}: "{item["title"]}"')
        print(f'    URL: {item["url"]}')

    conn.close()

if __name__ == '__main__':
    analyze_link_quality()
