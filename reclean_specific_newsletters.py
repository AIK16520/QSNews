"""
Re-clean specific newsletters that still have bad titles
"""

import sqlite3
import json
from clean_newsletter_links import clean_newsletter_links
from dotenv import load_dotenv

load_dotenv()

# Newsletter IDs that need re-cleaning
NEWSLETTER_IDS = [7, 14, 77, 113, 114, 151, 157, 158, 159]

def reclean_newsletters(newsletter_ids):
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    print(f"Re-cleaning {len(newsletter_ids)} newsletters with bad titles...")
    print()

    for nid in newsletter_ids:
        cursor.execute(
            'SELECT id, title, summary, extracted_links FROM newsletters WHERE id = ?',
            (nid,)
        )
        row = cursor.fetchone()

        if not row:
            print(f"Newsletter {nid} not found, skipping")
            continue

        newsletter_id = row[0]
        title = row[1]
        summary = row[2] or ""
        links = json.loads(row[3]) if row[3] else []

        print(f"Newsletter {newsletter_id}: {title[:60]}")
        print(f"  Original links: {len(links)}")

        # Clean links
        cleaned_links = clean_newsletter_links(
            newsletter_id,
            links,
            newsletter_summary=summary,
            use_ai=True
        )

        print(f"  Cleaned links: {len(cleaned_links)}")

        # Update database
        links_json = json.dumps(cleaned_links)
        cursor.execute(
            'UPDATE newsletters SET extracted_links = ? WHERE id = ?',
            (links_json, newsletter_id)
        )

    conn.commit()
    conn.close()

    print()
    print("[SUCCESS] Re-cleaning complete!")

if __name__ == '__main__':
    reclean_newsletters(NEWSLETTER_IDS)
