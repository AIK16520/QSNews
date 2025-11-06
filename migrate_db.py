"""
Database Migration Script
Adds new columns for review workflow to existing database.
"""

import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import config

def migrate_database():
    """Add new columns to articles table for review workflow."""
    db_path = config.DATABASE_PATH

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Run 'python src/main.py init-db' first to create the database.")
        return

    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(articles)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    print(f"Existing columns: {existing_columns}")

    # Columns to add
    new_columns = {
        'user_content': 'TEXT',
        'ai_instructions': 'TEXT',
        'generated_content': 'TEXT',
        'final_content': 'TEXT'
    }

    # Add each column if it doesn't exist
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}"
                print(f"Adding column: {column_name}")
                cursor.execute(sql)
                conn.commit()
                print(f"  [OK] Added {column_name}")
            except sqlite3.OperationalError as e:
                print(f"  [ERROR] Error adding {column_name}: {e}")
        else:
            print(f"  [SKIP] Column {column_name} already exists")

    conn.close()
    print("\nMigration complete!")
    print("You can now run the dashboard: streamlit run dashboard/app.py")

if __name__ == "__main__":
    migrate_database()
