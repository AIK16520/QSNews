"""
Migration Script: Update article statuses to new simplified system
Converts old statuses (pending, reviewed, skipped) to new system (included, not_included)
"""

import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import config

def migrate_statuses():
    """Update article statuses to new simplified system."""
    db_path = config.DATABASE_PATH

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print(f"Migrating article statuses: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get current status counts
    cursor.execute("SELECT status, COUNT(*) FROM articles GROUP BY status")
    old_statuses = cursor.fetchall()
    print(f"\nCurrent status counts:")
    for status, count in old_statuses:
        print(f"  {status}: {count}")

    # Update statuses
    # Keep 'included' as is
    # Convert everything else to 'not_included'
    cursor.execute("""
        UPDATE articles
        SET status = 'not_included'
        WHERE status NOT IN ('included', 'in_review', 'generated', 'finalized')
    """)

    updated_count = cursor.rowcount
    conn.commit()

    # Get new status counts
    cursor.execute("SELECT status, COUNT(*) FROM articles GROUP BY status")
    new_statuses = cursor.fetchall()
    print(f"\nNew status counts:")
    for status, count in new_statuses:
        print(f"  {status}: {count}")

    print(f"\n[OK] Updated {updated_count} articles to new status system")

    conn.close()

if __name__ == "__main__":
    migrate_statuses()
