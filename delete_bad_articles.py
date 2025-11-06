"""
Delete specific problematic articles by ID.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article

def delete_articles_by_ids(article_ids):
    """Delete articles by their IDs."""
    session = get_session()

    try:
        deleted_count = 0

        for article_id in article_ids:
            article = session.query(Article).get(article_id)
            if article:
                print(f"Deleting: {article.title[:60]}...")
                session.delete(article)
                deleted_count += 1
            else:
                print(f"Article ID {article_id} not found")

        session.commit()
        print(f"\nSuccessfully deleted {deleted_count} articles")
        return deleted_count

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    # IDs of additional problematic articles
    problem_ids = [337, 164]

    print(f"Deleting {len(problem_ids)} additional problematic articles...")
    print("-" * 60)

    deleted = delete_articles_by_ids(problem_ids)
    print(f"\nDatabase updated: {deleted} articles removed")
