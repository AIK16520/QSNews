"""
Remove all articles from a specific source from the database.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article

def remove_articles_by_source(source_name):
    """Remove all articles from a specific source."""
    session = get_session()

    try:
        # Find all articles from this source
        articles = session.query(Article).filter_by(source=source_name).all()

        if not articles:
            print(f"No articles found from source: {source_name}")
            return 0

        count = len(articles)
        print(f"Found {count} articles from '{source_name}'")

        # Confirm deletion
        confirm = input(f"Are you sure you want to delete {count} articles? (yes/no): ")

        if confirm.lower() == 'yes':
            # Delete all articles
            for article in articles:
                session.delete(article)

            session.commit()
            print(f"Successfully deleted {count} articles from '{source_name}'")
            return count
        else:
            print("Deletion cancelled.")
            return 0

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    # Remove articles from Analytics India Magazine
    source = "Analytics India Magazine"
    removed = remove_articles_by_source(source)

    if removed > 0:
        print(f"\nDatabase updated: {removed} articles removed")
