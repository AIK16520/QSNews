"""
Main CLI Entry Point
Provides command-line interface for the AI Newsletter Tool.

Commands:
    fetch               - Fetch articles from RSS feeds
    process             - Process fetched articles (scrape, classify, store)
    generate-review     - Generate pending review report
    weekly-summary      - Generate weekly summary report
    init-db             - Initialize database
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_fetch():
    """Fetch articles from RSS feeds."""
    from fetchers.rss_fetcher import fetch_all_rss, save_fetched_articles

    print("\n" + "="*80)
    print("FETCHING ARTICLES FROM RSS FEEDS")
    print("="*80 + "\n")

    start_time = datetime.now()

    # Fetch articles
    articles = fetch_all_rss()

    # Save to temp file
    save_fetched_articles(articles)

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "="*80)
    print(f" Fetch complete: {len(articles)} articles fetched in {elapsed:.1f}s")
    print("="*80 + "\n")


def cmd_process():
    """Process fetched articles (scrape, classify, store)."""
    from processors.pipeline import process_articles

    print("\n" + "="*80)
    print("PROCESSING ARTICLES")
    print("="*80 + "\n")

    start_time = datetime.now()

    # Process articles
    count = process_articles()

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "="*80)
    print(f" Processing complete: {count} articles added in {elapsed:.1f}s")
    print("="*80 + "\n")


def cmd_generate_review():
    """Generate pending review report."""
    from processors.report_generator import generate_pending_review

    print("\n" + "="*80)
    print("GENERATING PENDING REVIEW REPORT")
    print("="*80 + "\n")

    generate_pending_review()

    print("\n" + "="*80)
    print(" Report generated: outputs/pending_review.md")
    print("="*80 + "\n")


def cmd_weekly_summary():
    """Generate weekly summary report."""
    from processors.report_generator import generate_weekly_summary

    print("\n" + "="*80)
    print("GENERATING WEEKLY SUMMARY")
    print("="*80 + "\n")

    generate_weekly_summary()

    print("\n" + "="*80)
    print(" Summary generated: outputs/weekly_summary.md")
    print("="*80 + "\n")


def cmd_newsletter():
    """Generate newsletter draft with included articles and your analysis."""
    from processors.report_generator import generate_newsletter_draft

    print("\n" + "="*80)
    print("GENERATING NEWSLETTER DRAFT")
    print("="*80 + "\n")

    generate_newsletter_draft()

    print("\n" + "="*80)
    print(" Newsletter draft generated: outputs/newsletter_draft.md")
    print("="*80 + "\n")


def cmd_init_db():
    """Initialize database (create tables, seed data)."""
    from utils.database import init_database, get_session, Category, Industry, Article, Newsletter

    print("\n" + "="*80)
    print("INITIALIZING DATABASE")
    print("="*80 + "\n")

    init_database()

    # Print stats
    session = get_session()
    try:
        category_count = session.query(Category).count()
        industry_count = session.query(Industry).count()
        article_count = session.query(Article).count()
        newsletter_count = session.query(Newsletter).count()

        print(f"\nDatabase Statistics:")
        print(f"  Categories: {category_count}")
        print(f"  Industries: {industry_count}")
        print(f"  Articles: {article_count}")
        print(f"  Newsletters: {newsletter_count}")
    finally:
        session.close()

    print("\n" + "="*80)
    print(" Database initialized")
    print("="*80 + "\n")


def cmd_full_run():
    """Run complete workflow: fetch -> process -> generate report."""
    print("\n" + "="*80)
    print("FULL WORKFLOW: FETCH -> PROCESS -> REPORT")
    print("="*80 + "\n")

    overall_start = datetime.now()

    # 1. Fetch
    cmd_fetch()

    # 2. Process
    cmd_process()

    # 3. Generate report
    cmd_generate_review()

    # Summary
    elapsed = (datetime.now() - overall_start).total_seconds()
    print("\n" + "="*80)
    print(f" Full workflow complete in {elapsed:.1f}s")
    print("="*80 + "\n")


def cmd_fetch_newsletters():
    """Fetch newsletters from Gmail."""
    import os
    from processors.newsletter_pipeline import fetch_and_process_gmail_newsletters

    print("\n" + "="*80)
    print("FETCHING NEWSLETTERS FROM GMAIL")
    print("="*80 + "\n")
    
    # DEBUG: Check environment variables
    print(f"[MAIN DEBUG] Environment variables present:", flush=True)
    print(f"  - NEWSLETTER_GMAIL: {'✓' if os.getenv('NEWSLETTER_GMAIL') else '✗'}", flush=True)
    print(f"  - NEWSLETTER_PASS: {'✓' if os.getenv('NEWSLETTER_PASS') else '✗'}", flush=True)
    print(f"  - OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}", flush=True)
    print("", flush=True)

    start_time = datetime.now()

    count = fetch_and_process_gmail_newsletters(days_back=7)

    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "="*80)
    print(f" Fetch complete: {count} newsletters processed in {elapsed:.1f}s")
    print("="*80 + "\n")


def cmd_scrape_newsletter_archives():
    """Scrape newsletter archives for historic content."""
    from processors.newsletter_pipeline import scrape_and_process_archives

    print("\n" + "="*80)
    print("SCRAPING NEWSLETTER ARCHIVES")
    print("="*80 + "\n")

    start_time = datetime.now()

    count = scrape_and_process_archives(days_back=30)

    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "="*80)
    print(f" Scraping complete: {count} newsletters processed in {elapsed:.1f}s")
    print("="*80 + "\n")


def cmd_newsletter_full_run():
    """Run complete newsletter workflow: Gmail + Archives."""
    from processors.newsletter_pipeline import full_newsletter_pipeline

    print("\n" + "="*80)
    print("FULL NEWSLETTER WORKFLOW: GMAIL + ARCHIVES")
    print("="*80 + "\n")

    overall_start = datetime.now()

    results = full_newsletter_pipeline(
        fetch_gmail=True,
        scrape_archives=True,
        gmail_days_back=7,
        archive_days_back=30
    )

    elapsed = (datetime.now() - overall_start).total_seconds()
    print("\n" + "="*80)
    print(f" Full workflow complete in {elapsed:.1f}s")
    print(f" Gmail: {results['gmail']} | Archives: {results['archives']} | Total: {results['total']}")
    print("="*80 + "\n")


def print_usage():
    """Print usage information."""
    print("""
AI Newsletter Tool - CLI
=======================

Usage:
    python src/main.py <command>

Commands:
    ARTICLES:
    fetch               Fetch articles from RSS feeds
    process             Process fetched articles (scrape, classify, store)
    generate-review     Generate pending review report
    weekly-summary      Generate weekly summary report
    generate-newsletter Generate newsletter draft (included articles + your analysis)
    full-run            Run complete workflow (fetch -> process -> report)

    NEWSLETTERS:
    fetch-newsletters          Fetch newsletters from Gmail inbox
    scrape-newsletter-archives Scrape historic newsletters from public archives
    newsletter-full-run        Fetch Gmail + scrape archives (complete workflow)

    DATABASE:
    init-db             Initialize database (create tables, seed data)

Examples:
    python src/main.py fetch
    python src/main.py process
    python src/main.py newsletter-full-run

For the dashboard:
    streamlit run dashboard/app.py
""")


def main():
    """Main CLI entry point."""
    # Command mapping
    commands = {
        'fetch': cmd_fetch,
        'process': cmd_process,
        'generate-review': cmd_generate_review,
        'weekly-summary': cmd_weekly_summary,
        'generate-newsletter': cmd_newsletter,
        'init-db': cmd_init_db,
        'full-run': cmd_full_run,
        'fetch-newsletters': cmd_fetch_newsletters,
        'scrape-newsletter-archives': cmd_scrape_newsletter_archives,
        'newsletter-full-run': cmd_newsletter_full_run,
    }

    # Parse command
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    # Execute command
    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}", exc_info=True)
            sys.exit(1)
    elif command in ['-h', '--help', 'help']:
        print_usage()
    else:
        print(f"Unknown command: {command}\n")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
