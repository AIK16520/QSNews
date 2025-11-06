"""
Backfill Script: Add tags to existing newsletters
Runs once to extract and add tags to newsletters already in the database.
"""

import sys
import os
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.database import get_session, Newsletter
from processors.newsletter_processor import extract_newsletter_tags

def backfill_newsletter_tags():
    """
    Extract and save tags for all newsletters in the database that don't have tags yet.
    """
    session = get_session()

    print("=" * 80)
    print("BACKFILLING NEWSLETTER TAGS")
    print("=" * 80)
    print()

    try:
        # Get all newsletters without tags
        newsletters = session.query(Newsletter).filter(
            (Newsletter.tags == None) | (Newsletter.tags == [])
        ).all()

        total = len(newsletters)
        print(f"Found {total} newsletters without tags")
        print()

        if total == 0:
            print("[OK] All newsletters already have tags!")
            return

        updated = 0
        failed = 0

        for i, newsletter in enumerate(newsletters, 1):
            try:
                print(f"[{i}/{total}] Processing: {newsletter.title[:60]}...")

                # Extract tags
                tags = extract_newsletter_tags(newsletter.title, newsletter.summary or "")

                # Update newsletter
                newsletter.tags = tags
                session.commit()

                print(f"  [OK] Tags: {', '.join(tags)}")
                updated += 1

                # Rate limiting - wait 1 second between API calls
                if i < total:
                    time.sleep(1)

            except Exception as e:
                print(f"  [ERROR] Error: {e}")
                failed += 1
                session.rollback()
                continue

        print()
        print("=" * 80)
        print("BACKFILL COMPLETE")
        print("=" * 80)
        print(f"Total processed: {total}")
        print(f"Successfully updated: {updated}")
        print(f"Failed: {failed}")
        print()

    except Exception as e:
        print(f"Fatal error: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    print("\nNewsletter Tags Backfill Script\n")

    # Confirm before running
    response = input("This will extract tags for all newsletters without tags. Continue? (y/n): ")

    if response.lower() in ['y', 'yes']:
        start_time = datetime.now()
        backfill_newsletter_tags()
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Completed in {elapsed:.1f} seconds")
    else:
        print("Cancelled.")
