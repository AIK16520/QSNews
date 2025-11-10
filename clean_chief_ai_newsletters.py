"""
Clean Chief AI Office newsletters with investment fragments
"""

import sqlite3
import json
from clean_newsletter_links import clean_newsletter_links
from dotenv import load_dotenv

load_dotenv()

# Chief AI Office newsletters with bad links
NEWSLETTER_IDS = [164, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175]

def clean_chief_ai():
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    print(f"Cleaning {len(NEWSLETTER_IDS)} Chief AI Office newsletters...")
    print()

    total_removed = 0

    for nid in NEWSLETTER_IDS:
        cursor.execute(
            'SELECT id, title, summary, extracted_links FROM newsletters WHERE id = ?',
            (nid,)
        )
        row = cursor.fetchone()

        if not row:
            continue

        newsletter_id = row[0]
        title = row[1]
        summary = row[2] or ""
        links = json.loads(row[3]) if row[3] else []

        before_count = len(links)

        # Clean with updated filters
        cleaned_links = clean_newsletter_links(
            newsletter_id,
            links,
            newsletter_summary=summary,
            use_ai=False  # No AI needed for filtering
        )

        after_count = len(cleaned_links)
        removed = before_count - after_count

        if removed > 0:
            title_safe = title.encode('ascii', 'ignore').decode('ascii')[:50]
            print(f"Newsletter {newsletter_id}: {title_safe}")
            print(f"  Removed {removed} investment fragment links")
            total_removed += removed

        # Update database
        links_json = json.dumps(cleaned_links)
        cursor.execute(
            'UPDATE newsletters SET extracted_links = ? WHERE id = ?',
            (links_json, newsletter_id)
        )

    conn.commit()
    conn.close()

    print()
    print("="*80)
    print(f"[SUCCESS] Removed {total_removed} investment fragment links!")
    print("="*80)

if __name__ == '__main__':
    clean_chief_ai()
