"""
Report Generator Module
Generates markdown reports for article review and weekly summaries.
"""

import logging
import os
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.database import Article, Category, Industry, get_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_pending_review(
    session: Optional[Session] = None,
    output_file: str = 'outputs/pending_review.md'
) -> None:
    """
    Generate a markdown report of all pending articles.
    Groups articles by category.

    Args:
        session: Database session (creates new one if None)
        output_file: Path to output markdown file
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Query pending articles
        articles = session.query(Article).filter_by(status='pending').order_by(
            Article.category_id, Article.published_date.desc()
        ).all()

        # Group by category
        articles_by_category = {}
        for article in articles:
            category_name = article.category.name if article.category else 'Uncategorized'
            if category_name not in articles_by_category:
                articles_by_category[category_name] = []
            articles_by_category[category_name].append(article)

        # Generate markdown
        md_lines = []
        md_lines.append("# Pending Articles for Review\n")
        md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        md_lines.append(f"**Total Articles:** {len(articles)}\n")
        md_lines.append("---\n")

        # Articles by category
        for category_name in sorted(articles_by_category.keys()):
            category_articles = articles_by_category[category_name]
            md_lines.append(f"\n## {category_name} ({len(category_articles)})\n")

            for article in category_articles:
                md_lines.append(f"\n### {article.title}\n")
                md_lines.append(f"**Source:** {article.source} | **Date:** {article.published_date.strftime('%Y-%m-%d') if article.published_date else 'N/A'}\n")

                # Industries
                if article.industries:
                    industries_str = ', '.join([ind.name for ind in article.industries])
                    md_lines.append(f"**Industries:** {industries_str}\n")

                # Summary
                if article.summary:
                    md_lines.append(f"\n{article.summary}\n")

                # URL
                md_lines.append(f"\n[Read more]({article.url})\n")
                md_lines.append("\n---\n")

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)

        logger.info(f"Generated pending review report: {output_file} ({len(articles)} articles)")

    finally:
        if close_session:
            session.close()


def generate_weekly_summary(
    session: Optional[Session] = None,
    output_file: str = 'outputs/weekly_summary.md',
    days: int = 7
) -> None:
    """
    Generate a weekly summary report with statistics and breakdowns.

    Args:
        session: Database session (creates new one if None)
        output_file: Path to output markdown file
        days: Number of days to include in summary
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query articles from last week
        articles = session.query(Article).filter(
            Article.fetched_date >= start_date
        ).all()

        # Statistics
        total_articles = len(articles)

        # Category breakdown
        category_counts = Counter()
        for article in articles:
            if article.category:
                category_counts[article.category.name] += 1

        # Industry breakdown
        industry_counts = Counter()
        for article in articles:
            for industry in article.industries:
                industry_counts[industry.name] += 1

        # Source breakdown
        source_counts = Counter([article.source for article in articles])

        # Status breakdown
        status_counts = Counter([article.status for article in articles])

        # Generate markdown
        md_lines = []
        md_lines.append("# Weekly Summary Report\n")
        md_lines.append(f"**Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")
        md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        md_lines.append("\n---\n")

        # Overview
        md_lines.append("\n## Overview\n")
        md_lines.append(f"- **Total Articles Fetched:** {total_articles}\n")
        md_lines.append(f"- **Pending Review:** {status_counts.get('pending', 0)}\n")
        md_lines.append(f"- **Reviewed:** {status_counts.get('reviewed', 0)}\n")
        md_lines.append(f"- **Included:** {status_counts.get('included', 0)}\n")
        md_lines.append(f"- **Skipped:** {status_counts.get('skipped', 0)}\n")

        # Category breakdown
        md_lines.append("\n## Articles by Category\n")
        for category, count in category_counts.most_common():
            percentage = (count / total_articles * 100) if total_articles > 0 else 0
            bar = '�' * int(percentage / 5)  # Visual bar chart
            md_lines.append(f"- **{category}:** {count} ({percentage:.1f}%) {bar}\n")

        # Industry breakdown
        md_lines.append("\n## Articles by Industry\n")
        for industry, count in industry_counts.most_common(10):  # Top 10
            md_lines.append(f"- {industry}: {count}\n")

        # Top sources
        md_lines.append("\n## Top Sources\n")
        for source, count in source_counts.most_common(10):  # Top 10
            md_lines.append(f"- {source}: {count}\n")

        # Recent highlights (top 5 by date)
        md_lines.append("\n## Recent Highlights\n")
        recent_articles = sorted(
            [a for a in articles if a.published_date],
            key=lambda x: x.published_date,
            reverse=True
        )[:5]

        for article in recent_articles:
            md_lines.append(f"\n### {article.title}\n")
            md_lines.append(f"*{article.source} - {article.published_date.strftime('%Y-%m-%d')}*\n")
            if article.summary:
                md_lines.append(f"\n{article.summary}\n")
            md_lines.append(f"\n[Read more]({article.url})\n")

        # Footer
        md_lines.append("\n---\n")
        md_lines.append("\n*For detailed review, see [pending_review.md](pending_review.md)*\n")

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)

        logger.info(f"Generated weekly summary: {output_file} ({total_articles} articles)")

    finally:
        if close_session:
            session.close()


def generate_newsletter_draft(
    session: Optional[Session] = None,
    output_file: str = 'outputs/newsletter_draft.md'
) -> None:
    """
    Generate a newsletter draft with ONLY included articles and your analysis.

    Args:
        session: Database session (creates new one if None)
        output_file: Path to output markdown file
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Query articles in workflow (included, generated, finalized)
        articles = session.query(Article).filter(
            Article.status.in_(['included', 'generated', 'finalized'])
        ).order_by(Article.category_id, Article.published_date.desc()).all()

        # Group by category
        articles_by_category = {}
        for article in articles:
            category_name = article.category.name if article.category else 'Uncategorized'
            if category_name not in articles_by_category:
                articles_by_category[category_name] = []
            articles_by_category[category_name].append(article)

        # Generate markdown
        md_lines = []
        md_lines.append("# Newsletter Draft\n")
        md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        md_lines.append(f"**Total Articles Included:** {len(articles)}\n")
        md_lines.append("\n---\n")

        if not articles:
            md_lines.append("\n*No articles marked as 'included' yet.*\n")
            md_lines.append("\n*Use the dashboard to mark articles as 'included' and add your analysis.*\n")
        else:
            # Articles by category
            for category_name in sorted(articles_by_category.keys()):
                category_articles = articles_by_category[category_name]
                md_lines.append(f"\n## {category_name} ({len(category_articles)})\n")

                for article in category_articles:
                    md_lines.append(f"\n### {article.title}\n")

                    # Source and date
                    md_lines.append(f"**Source:** {article.source}")
                    if article.published_date:
                        md_lines.append(f" | **Date:** {article.published_date.strftime('%Y-%m-%d')}")
                    md_lines.append("\n")

                    # Industries
                    if article.industries:
                        industries_str = ', '.join([ind.name for ind in article.industries])
                        md_lines.append(f"**Industries:** {industries_str}\n")

                    # YOUR ANALYSIS (highlight this!)
                    if article.your_analysis:
                        md_lines.append(f"\n**Your Analysis:**\n")
                        md_lines.append(f"> {article.your_analysis}\n")

                    # Summary
                    if article.summary:
                        md_lines.append(f"\n**Summary:** {article.summary}\n")

                    # URL
                    md_lines.append(f"\n[Read full article]({article.url})\n")
                    md_lines.append("\n---\n")

        # Footer
        md_lines.append(f"\n*Newsletter draft generated with {len(articles)} included articles*\n")

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)

        logger.info(f"Generated newsletter draft: {output_file} ({len(articles)} included articles)")

    finally:
        if close_session:
            session.close()


def main():
    """Test report generation."""
    print("Generating Reports\n")

    # Generate pending review report
    print("Generating pending review report...")
    generate_pending_review()

    # Generate weekly summary
    print("Generating weekly summary...")
    generate_weekly_summary()

    print("\n Reports generated successfully")
    print("  - outputs/pending_review.md")
    print("  - outputs/weekly_summary.md")


if __name__ == "__main__":
    main()
