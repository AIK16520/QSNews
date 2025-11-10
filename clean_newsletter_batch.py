"""
Clean newsletters in a specific ID range
"""

import sys
import sqlite3
import json
from clean_newsletter_links import clean_newsletter_links
from dotenv import load_dotenv

load_dotenv()

def clean_batch(start_id: int, end_id: int, dry_run: bool = False, use_ai: bool = True):
    """Clean newsletters with IDs in the range [start_id, end_id]."""
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    # Get newsletters in range
    cursor.execute(
        'SELECT id, title, summary, extracted_links FROM newsletters WHERE id >= ? AND id <= ? AND extracted_links IS NOT NULL ORDER BY id',
        (start_id, end_id)
    )
    newsletters = cursor.fetchall()

    print(f"Processing {len(newsletters)} newsletters (IDs {start_id}-{end_id})")
    print(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}, AI: {'ON' if use_ai else 'OFF'}")
    print()

    total_original = 0
    total_cleaned = 0

    for row in newsletters:
        newsletter_id = row[0]
        title = row[1]
        summary = row[2] or ""
        links = json.loads(row[3]) if row[3] else []

        total_original += len(links)

        # Clean links
        cleaned_links = clean_newsletter_links(
            newsletter_id,
            links,
            newsletter_summary=summary,
            use_ai=use_ai
        )

        total_cleaned += len(cleaned_links)

        # Update database
        if not dry_run:
            links_json = json.dumps(cleaned_links)
            cursor.execute(
                'UPDATE newsletters SET extracted_links = ? WHERE id = ?',
                (links_json, newsletter_id)
            )

    if not dry_run:
        conn.commit()
        print(f"\n[SUCCESS] Changes committed to database")
    else:
        print(f"\n[DRY RUN] No changes made")

    conn.close()

    print(f"\n{'='*80}")
    print(f"BATCH SUMMARY (IDs {start_id}-{end_id})")
    print(f"{'='*80}")
    print(f"Newsletters processed: {len(newsletters)}")
    print(f"Original links: {total_original}")
    print(f"Cleaned links: {total_cleaned}")
    print(f"Links removed: {total_original - total_cleaned}")
    print(f"Reduction: {(total_original - total_cleaned) / total_original * 100:.1f}%")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Clean newsletter batch')
    parser.add_argument('start_id', type=int, help='Start newsletter ID')
    parser.add_argument('end_id', type=int, help='End newsletter ID')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI')

    args = parser.parse_args()

    clean_batch(
        args.start_id,
        args.end_id,
        dry_run=args.dry_run,
        use_ai=not args.no_ai
    )
