#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to regenerate all newsletter summaries without embedded links.
This fixes the issue of truncated URLs in summaries.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.database import get_session, Newsletter, init_database
from src.processors.newsletter_processor import generate_newsletter_summary
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def regenerate_all_summaries(batch_size: int = 10, limit: int = None):
    """
    Regenerate summaries for all newsletters without embedded links.

    Args:
        batch_size: Number of newsletters to commit at once
        limit: Optional limit on number of newsletters to process
    """
    session = get_session()

    try:
        # Initialize database
        init_database()

        logger.info("="*80)
        logger.info("REGENERATING NEWSLETTER SUMMARIES (WITHOUT EMBEDDED LINKS)")
        logger.info("="*80)

        # Get all newsletters that have content
        query = session.query(Newsletter).filter(
            (Newsletter.full_content != None) | (Newsletter.plain_text != None)
        ).order_by(Newsletter.id)

        if limit:
            query = query.limit(limit)

        newsletters = query.all()

        total = len(newsletters)

        logger.info(f"Total newsletters with content: {total}")
        logger.info("="*80 + "\n")

        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
            logger.error("Please set OPENAI_API_KEY to regenerate summaries")
            return

        logger.info(f"✓ OpenAI API key found\n")

        updated_count = 0
        failed_count = 0

        for i, newsletter in enumerate(newsletters, 1):
            try:
                logger.info(f"[{i}/{total}] Processing: {newsletter.source} - {newsletter.title[:60]}...")

                # Build newsletter data dict for summary generation
                newsletter_data = {
                    'source': newsletter.source,
                    'email_subject': newsletter.email_subject or newsletter.title,
                    'html_content': newsletter.full_content,
                    'plain_text': newsletter.plain_text,
                    'extracted_links': newsletter.extracted_links if newsletter.extracted_links else []
                }

                # Generate new summary (without embedded links)
                old_summary = newsletter.summary
                new_summary = generate_newsletter_summary(newsletter_data)

                # Update the newsletter
                newsletter.summary = new_summary

                logger.info(f"  Old length: {len(old_summary)} chars")
                logger.info(f"  New length: {len(new_summary)} chars")

                updated_count += 1

                # Commit in batches
                if updated_count % batch_size == 0:
                    session.commit()
                    logger.info(f"  ✓ Committed batch (total updated: {updated_count})\n")
                else:
                    logger.info("")

            except Exception as e:
                logger.error(f"  ✗ Error: {e}\n")
                failed_count += 1
                continue

        # Final commit
        if updated_count > 0:
            session.commit()
            logger.info(f"✓ Final commit complete\n")

        # Summary
        logger.info("="*80)
        logger.info("UPDATE SUMMARY")
        logger.info("="*80)
        logger.info(f"Total newsletters: {total}")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info("="*80 + "\n")

        logger.info("✓ All summaries have been regenerated without embedded links!")
        logger.info("  Links will now be displayed separately in the UI.")

    except Exception as e:
        logger.error(f"Error in batch update: {e}")
        session.rollback()
        logger.info("Rolled back changes due to error")

    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Regenerate newsletter summaries without embedded links'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for commits (default: 10)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of newsletters to process (for testing)'
    )

    args = parser.parse_args()

    regenerate_all_summaries(batch_size=args.batch_size, limit=args.limit)
