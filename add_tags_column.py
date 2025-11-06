"""
Add tags column to newsletters table
"""

import sqlite3
import sys

def add_tags_column():
    """Add tags column to newsletters table if it doesn't exist."""
    db_path = 'data/articles.db'

    print(f"Connecting to database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("PRAGMA table_info(newsletters)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'tags' in columns:
            print("[OK] Column 'tags' already exists in newsletters table")
        else:
            print("Adding 'tags' column to newsletters table...")
            cursor.execute("ALTER TABLE newsletters ADD COLUMN tags TEXT")
            conn.commit()
            print("[OK] Column 'tags' added successfully")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    add_tags_column()
