"""
Verify cleaned newsletter links before and after
Shows side-by-side comparison
"""

import sqlite3
import json

def show_comparison(newsletter_id: int):
    """Show before/after comparison for a specific newsletter."""
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, title, extracted_links FROM newsletters WHERE id = ?', (newsletter_id,))
    row = cursor.fetchone()

    if not row:
        print(f"Newsletter {newsletter_id} not found")
        return

    print(f"\n=== Newsletter {row[0]}: {row[1][:60]}... ===")

    links = json.loads(row[2]) if row[2] else []

    # Show all links with their titles and URLs
    print(f"\nTotal links: {len(links)}")
    print("\n" + "="*100)

    for i, link in enumerate(links[:15], 1):  # Show first 15
        title = link.get('title', 'NO TITLE')
        url = link.get('url', 'NO URL')

        # Check if URL has tracking parameters
        has_tracking = 'utm_' in url or 'gaa_' in url

        # Check if title is bad
        is_bad = len(title) <= 10 or title.lower() in [
            'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said',
            'reports', 'pulled', 'backlash', 'became', 'signing', 'link',
            'here', 'read more', 'ad spot'
        ]

        print(f"\n{i}. TITLE: {title}")
        if is_bad:
            print(f"   [!] BAD TITLE (needs improvement)")

        # Show URL (truncated)
        if len(url) > 90:
            print(f"   URL:  {url[:90]}...")
        else:
            print(f"   URL:  {url}")

        if has_tracking:
            print(f"   [!] HAS TRACKING PARAMETERS")

    conn.close()

if __name__ == '__main__':
    # Show a few sample newsletters
    for newsletter_id in [1, 2, 3]:
        show_comparison(newsletter_id)
