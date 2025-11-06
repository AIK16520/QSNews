"""
Check all sources for bundled/multi-topic article issues.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Article
from sqlalchemy import func

def check_all_sources():
    """Check all sources for quality issues."""
    session = get_session()

    try:
        # Get all unique sources
        sources = session.query(Article.source).distinct().all()
        sources = [s[0] for s in sources]

        print(f"Checking {len(sources)} sources for quality issues...")
        print("=" * 80)

        # Multi-topic indicators
        topic_indicators = [
            'various topics',
            'the article discusses various',
            'additionally, it touches',
            'also discusses',
            'among other things',
            'multiple developments',
            'several topics',
            'range of topics',
            'variety of subjects'
        ]

        all_problem_articles = []
        source_report = []

        for source in sorted(sources):
            # Get all articles from this source
            articles = session.query(Article).filter_by(source=source).all()

            problem_count = 0
            problem_ids = []

            for article in articles:
                if article.summary:
                    # Check for bundling indicators
                    has_issues = any(indicator in article.summary.lower() for indicator in topic_indicators)

                    if has_issues:
                        problem_count += 1
                        problem_ids.append(article.id)
                        all_problem_articles.append({
                            'id': article.id,
                            'source': source,
                            'title': article.title,
                            'url': article.url
                        })

            if problem_count > 0:
                percentage = (problem_count / len(articles)) * 100
                source_report.append({
                    'source': source,
                    'total': len(articles),
                    'problems': problem_count,
                    'percentage': percentage,
                    'ids': problem_ids
                })

        # Print report
        print("\nSOURCES WITH QUALITY ISSUES:")
        print("-" * 80)

        if source_report:
            # Sort by problem count
            source_report.sort(key=lambda x: x['problems'], reverse=True)

            for report in source_report:
                print(f"\n{report['source']}:")
                print(f"  Total articles: {report['total']}")
                print(f"  Problem articles: {report['problems']} ({report['percentage']:.1f}%)")
                print(f"  Article IDs: {report['ids']}")
        else:
            print("No quality issues found!")

        # Overall summary
        print("\n" + "=" * 80)
        print("OVERALL SUMMARY:")
        print(f"Total sources checked: {len(sources)}")
        print(f"Sources with issues: {len(source_report)}")
        print(f"Total problem articles: {len(all_problem_articles)}")

        # Save problem article IDs to file
        if all_problem_articles:
            with open('data/problem_articles.txt', 'w') as f:
                f.write("Problem Article IDs:\n")
                f.write("=" * 80 + "\n\n")
                for article in all_problem_articles:
                    f.write(f"ID: {article['id']}\n")
                    f.write(f"Source: {article['source']}\n")
                    f.write(f"Title: {article['title'][:80]}\n")
                    f.write(f"URL: {article['url']}\n")
                    f.write("-" * 80 + "\n")

            print(f"\nProblem article details saved to: data/problem_articles.txt")

        return all_problem_articles

    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        session.close()


if __name__ == "__main__":
    problem_articles = check_all_sources()
