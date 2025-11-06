"""
Check all sources in the database.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article
from sqlalchemy import func

def check_sources():
    """List all sources in the database."""
    session = get_session()

    try:
        # Get all unique sources and their counts
        sources = session.query(Article.source, func.count(Article.id)).group_by(Article.source).order_by(func.count(Article.id).desc()).all()

        print('All Sources in database:')
        print('-' * 60)
        for source, count in sources:
            print(f'{source}: {count} articles')

        print('-' * 60)
        print(f'Total sources: {len(sources)}')

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    check_sources()
