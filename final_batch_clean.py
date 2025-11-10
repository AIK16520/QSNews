"""
Final batch cleaning of promotional links
"""

import sqlite3
import json
from clean_newsletter_links import clean_newsletter_links
from dotenv import load_dotenv

load_dotenv()

NEWSLETTER_IDS = [87, 89, 90, 96, 100, 110, 114, 149, 150, 151, 154, 157, 158, 159, 160, 161]

def final_batch_clean():
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    print(f"Final batch cleaning of {len(NEWSLETTER_IDS)} newsletters...")
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

        # Clean with aggressive promotional filtering
        cleaned_links = clean_newsletter_links(
            newsletter_id,
            links,
            newsletter_summary=summary,
            use_ai=False  # No AI needed for promotional filtering
        )

        after_count = len(cleaned_links)
        removed = before_count - after_count

        if removed > 0:
            print(f"Newsletter {newsletter_id}: Removed {removed} promotional links")
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
    print(f"[SUCCESS] Removed {total_removed} promotional links total!")
    print("="*80)

if __name__ == '__main__':
    final_batch_clean()
