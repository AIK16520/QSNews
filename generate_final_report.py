"""
Generate comprehensive final report on newsletter link cleaning
"""

import sqlite3
import json

def generate_final_report():
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    # Get all newsletters with links
    cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
    newsletters = cursor.fetchall()

    print("=" * 100)
    print("NEWSLETTER LINK CLEANING - FINAL REPORT")
    print("=" * 100)
    print()

    # Overall statistics
    total_newsletters = len(newsletters)
    total_links = 0
    links_with_tracking = 0
    links_with_short_titles = 0
    links_with_bad_titles = 0

    BAD_TITLE_PATTERNS = [
        'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'reports',
        'pulled', 'backlash', 'became', 'signing', 'relaunching', 'announced',
        'released', 'launched', 'unveiled', 'revealed', 'confirmed', 'denied',
        'link', 'here', 'click here', 'read more', 'see more', 'ad spot'
    ]

    for row in newsletters:
        links = json.loads(row[3]) if row[3] else []
        total_links += len(links)

        for link in links:
            url = link.get('url', '')
            title = link.get('title', '')

            # Check for tracking
            if 'utm_' in url or 'gaa_' in url:
                links_with_tracking += 1

            # Check for short titles
            if len(title) <= 10:
                links_with_short_titles += 1

            # Check for bad titles
            if title.lower() in BAD_TITLE_PATTERNS:
                links_with_bad_titles += 1

    print(f"NEWSLETTERS PROCESSED: {total_newsletters}")
    print(f"TOTAL LINKS: {total_links}")
    print()

    print("LINK QUALITY METRICS:")
    print(f"  Links with tracking parameters: {links_with_tracking} ({links_with_tracking/total_links*100:.1f}%)")
    print(f"  Links with short titles (<=10 chars): {links_with_short_titles} ({links_with_short_titles/total_links*100:.1f}%)")
    print(f"  Links with bad/uninformative titles: {links_with_bad_titles} ({links_with_bad_titles/total_links*100:.1f}%)")
    print()

    # Sample cleaned newsletters
    print("=" * 100)
    print("SAMPLE CLEANED NEWSLETTERS (First 3)")
    print("=" * 100)

    cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE id <= 3 AND extracted_links IS NOT NULL')
    sample_newsletters = cursor.fetchall()

    for row in sample_newsletters:
        newsletter_id = row[0]
        title = row[1]
        source = row[2]
        links = json.loads(row[3]) if row[3] else []

        print(f"\nNewsletter {newsletter_id}: {title[:60]}")
        print(f"Source: {source}")
        print(f"Links: {len(links)}")
        print()

        # Show first 5 links
        for i, link in enumerate(links[:5], 1):
            link_title = link.get('title', 'NO TITLE')
            url = link.get('url', 'NO URL')

            print(f"  {i}. {link_title}")
            if len(url) > 80:
                print(f"     {url[:80]}...")
            else:
                print(f"     {url}")

    # Links by source
    print()
    print("=" * 100)
    print("LINKS BY NEWSLETTER SOURCE")
    print("=" * 100)

    cursor.execute("""
        SELECT source, COUNT(*) as newsletter_count
        FROM newsletters
        WHERE extracted_links IS NOT NULL
        GROUP BY source
        ORDER BY newsletter_count DESC
    """)
    sources = cursor.fetchall()

    for source, count in sources:
        # Get total links for this source
        cursor.execute('SELECT extracted_links FROM newsletters WHERE source = ? AND extracted_links IS NOT NULL', (source,))
        source_newsletters = cursor.fetchall()

        source_links = 0
        for snl in source_newsletters:
            links = json.loads(snl[0]) if snl[0] else []
            source_links += len(links)

        print(f"  {source}: {count} newsletters, {source_links} total links")

    conn.close()

    print()
    print("=" * 100)
    print("CLEANING COMPLETE!")
    print("=" * 100)

if __name__ == '__main__':
    generate_final_report()
