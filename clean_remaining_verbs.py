"""
Clean newsletters with remaining single-verb titles
"""

import sqlite3
import json
from clean_newsletter_links import clean_newsletter_links
from dotenv import load_dotenv

load_dotenv()

# Newsletters with confirmed single verbs
NEWSLETTER_IDS = [10, 18, 74]  # has 'opened', 'opening', 'Sign up for free here'

def clean_remaining():
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    print(f"Cleaning {len(NEWSLETTER_IDS)} newsletters with remaining bad links...")
    print()

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

        title_safe = title.encode('ascii', 'ignore').decode('ascii')[:60]
        print(f"Newsletter {newsletter_id}: {title_safe}")
        print(f"  Before: {len(links)} links")

        # Clean with updated logic
        cleaned_links = clean_newsletter_links(
            newsletter_id,
            links,
            newsletter_summary=summary,
            use_ai=True
        )

        print(f"  After: {len(cleaned_links)} links")

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
    print("[SUCCESS] Cleaning complete!")
    print("="*80)

if __name__ == '__main__':
    clean_remaining()
