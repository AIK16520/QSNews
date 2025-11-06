"""
Check Wired AI articles for quality issues.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article

def check_wired_articles():
    """Check all Wired AI articles."""
    session = get_session()

    try:
        # Get all Wired AI articles
        wired_articles = session.query(Article).filter_by(source='Wired AI').all()

        print(f"Found {len(wired_articles)} articles from Wired AI")
        print("=" * 80)

        problem_articles = []

        for i, article in enumerate(wired_articles, 1):
            try:
                # Basic info
                title = article.title.encode('ascii', 'ignore').decode('ascii') if article.title else 'No title'
                print(f"\n{i}. {title[:80]}")
                print(f"   URL: {article.url}")

                # Check summary
                if article.summary:
                    summary_preview = article.summary[:300]

                    # Check for multiple topics (indicators of bundled articles)
                    topic_indicators = [
                        'various topics',
                        'including',
                        'additionally, it touches',
                        'also discusses',
                        'among other things',
                        'the article discusses various',
                        'benefits of air-popped popcorn',  # Specific to the bad article
                        'dracula movie'  # Specific indicator
                    ]

                    has_issues = any(indicator in article.summary.lower() for indicator in topic_indicators)

                    if has_issues:
                        print(f"   WARNING: Likely bundled/multi-topic article")
                        print(f"   Summary: {summary_preview}...")
                        problem_articles.append(article.id)
                    else:
                        print(f"   OK - Single topic article")

                # Check content length
                if article.full_content:
                    content_length = len(article.full_content)
                    print(f"   Content length: {content_length} chars")

                print("-" * 80)

            except Exception as e:
                print(f"   Error checking article: {e}")
                continue

        print(f"\nSummary:")
        print(f"Total articles: {len(wired_articles)}")
        print(f"Problem articles: {len(problem_articles)}")

        if problem_articles:
            print(f"\nArticle IDs with issues: {problem_articles}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    check_wired_articles()
