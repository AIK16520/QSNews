"""
Show before/after results of newsletter link cleaning
"""

import sqlite3
import json

def show_sample_cleaned_links():
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    # Get a few cleaned newsletters
    cursor.execute('SELECT id, title, extracted_links FROM newsletters WHERE id <= 3 AND extracted_links IS NOT NULL')
    newsletters = cursor.fetchall()

    for row in newsletters:
        newsletter_id = row[0]
        title = row[1]
        links = json.loads(row[2]) if row[2] else []

        print(f"\n{'='*100}")
        print(f"Newsletter {newsletter_id}: {title[:70]}")
        print(f"{'='*100}")
        print(f"Total links after cleaning: {len(links)}")
        print()

        # Show first 10 links
        for i, link in enumerate(links[:10], 1):
            link_title = link.get('title', 'NO TITLE')
            url = link.get('url', 'NO URL')

            print(f"{i}. {link_title}")

            # Show URL (check if tracking params are gone)
            has_tracking = 'utm_' in url or 'gaa_' in url
            if has_tracking:
                print(f"   [WARNING] Still has tracking: {url[:90]}")
            else:
                if len(url) > 90:
                    print(f"   URL: {url[:90]}...")
                else:
                    print(f"   URL: {url}")

    conn.close()

    # Overall statistics
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM newsletters WHERE extracted_links IS NOT NULL')
    total_newsletters = cursor.fetchone()[0]

    cursor.execute('SELECT id, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
    all_newsletters = cursor.fetchall()

    total_links = 0
    links_with_tracking = 0
    short_titles = 0

    for row in all_newsletters:
        links = json.loads(row[1]) if row[1] else []
        total_links += len(links)

        for link in links:
            url = link.get('url', '')
            title = link.get('title', '')

            if 'utm_' in url or 'gaa_' in url:
                links_with_tracking += 1

            if len(title) <= 10:
                short_titles += 1

    print(f"\n{'='*100}")
    print(f"OVERALL STATISTICS")
    print(f"{'='*100}")
    print(f"Total newsletters with links: {total_newsletters}")
    print(f"Total links: {total_links}")
    print(f"Links still with tracking parameters: {links_with_tracking} ({links_with_tracking/total_links*100:.1f}%)")
    print(f"Links with short/bad titles (<=10 chars): {short_titles} ({short_titles/total_links*100:.1f}%)")

    conn.close()

if __name__ == '__main__':
    show_sample_cleaned_links()
