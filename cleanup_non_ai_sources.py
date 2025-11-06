"""
Remove articles from non-AI sources from the database.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article
from sqlalchemy import func

def cleanup_non_ai_sources():
    """Remove articles from non-AI sources."""
    session = get_session()

    # List of non-AI sources to remove
    sources_to_remove = [
        # From config removal
        "StrictlyVC",
        "Crunchbase News",
        "Ars Technica All",
        "Bloomberg Tech",
        "Business Insider",
        "Business Insrunider",  # Typo version
        "Wired Business",
        "VentureBeat",  # General, not VentureBeat AI
        "TechCrunch",  # General, not TechCrunch AI
        "The Verge",  # General, not The Verge AI
        "Engadget",
        "Gizmodo",
        "The New Stack",
        "Silicon Republic",
        "TechSpot",
        "Techmeme",
        "NYT Technology",
        "Reuters Tech",
        "Databricks",
        "Anaconda",
        "Netflix Tech",
        "Datanami",
        "insideBIGDATA",
        "Stack Overflow Blog",
        "DEV Community",
        "Quanta Magazine",
        # Additional sources to remove
        "The Guardian AI",  # User requested
        "404 Media",  # Not AI-focused
        "DeepMind Blog",  # Might be inactive/non-AI
        "Hugging Face",  # Not a news source
    ]

    try:
        total_deleted = 0

        print("Checking database for non-AI sources...")
        print("=" * 80)

        # Get all sources in database
        all_sources = session.query(Article.source, func.count(Article.id)).group_by(Article.source).all()

        print(f"\nFound {len(all_sources)} unique sources in database")
        print("-" * 80)

        for source_name in sources_to_remove:
            articles = session.query(Article).filter_by(source=source_name).all()

            if articles:
                count = len(articles)
                print(f"Deleting {count} articles from: {source_name}")

                for article in articles:
                    session.delete(article)

                total_deleted += count
            else:
                print(f"No articles found from: {source_name}")

        # Commit all deletions
        session.commit()

        print("\n" + "=" * 80)
        print(f"CLEANUP COMPLETE")
        print(f"Total articles deleted: {total_deleted}")
        print("=" * 80)

        # Show remaining sources
        print("\nRemaining sources in database:")
        print("-" * 80)
        remaining_sources = session.query(Article.source, func.count(Article.id)).group_by(Article.source).order_by(func.count(Article.id).desc()).all()

        for source, count in remaining_sources:
            print(f"{source}: {count} articles")

        print("-" * 80)
        print(f"Total remaining sources: {len(remaining_sources)}")
        print(f"Total remaining articles: {sum(count for _, count in remaining_sources)}")

        return total_deleted

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    print("Starting cleanup of non-AI sources...")
    print()

    deleted = cleanup_non_ai_sources()

    print(f"\nDatabase cleanup complete: {deleted} articles removed")
