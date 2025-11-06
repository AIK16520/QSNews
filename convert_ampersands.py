"""
Convert all & symbols to "and" in article titles, summaries, and content.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article

def convert_ampersands():
    """Replace all & with 'and' in articles."""
    session = get_session()

    try:
        # Get all articles
        articles = session.query(Article).all()

        updated_count = 0

        print(f"Checking {len(articles)} articles...")
        print("-" * 60)

        for article in articles:
            updated = False

            # Update title
            if article.title and '&' in article.title:
                old_title = article.title
                article.title = article.title.replace('&', 'and')
                print(f"Title: {old_title[:50]}... -> {article.title[:50]}...")
                updated = True

            # Update summary
            if article.summary and '&' in article.summary:
                article.summary = article.summary.replace('&', 'and')
                updated = True

            # Update full content
            if article.full_content and '&' in article.full_content:
                article.full_content = article.full_content.replace('&', 'and')
                updated = True

            # Update source
            if article.source and '&' in article.source:
                old_source = article.source
                article.source = article.source.replace('&', 'and')
                print(f"Source: {old_source} -> {article.source}")
                updated = True

            # Update your_analysis
            if article.your_analysis and '&' in article.your_analysis:
                article.your_analysis = article.your_analysis.replace('&', 'and')
                updated = True

            # Update user_content
            if article.user_content and '&' in article.user_content:
                article.user_content = article.user_content.replace('&', 'and')
                updated = True

            # Update generated_content
            if article.generated_content and '&' in article.generated_content:
                article.generated_content = article.generated_content.replace('&', 'and')
                updated = True

            # Update final_content
            if article.final_content and '&' in article.final_content:
                article.final_content = article.final_content.replace('&', 'and')
                updated = True

            if updated:
                updated_count += 1

        # Commit changes
        session.commit()

        print("-" * 60)
        print(f"Successfully updated {updated_count} articles")
        print(f"Converted all '&' to 'and'")

        return updated_count

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    updated = convert_ampersands()
    print(f"\nDatabase updated: {updated} articles modified")
