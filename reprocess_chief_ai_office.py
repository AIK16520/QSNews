#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to reprocess Chief AI Office newsletters with updated link filters.
This will remove promotional links and regenerate summaries.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.database import get_session, Newsletter, init_database
from src.utils.link_extractor import extract_and_explain_links
from src.processors.newsletter_processor import generate_newsletter_summary, extract_newsletter_tags, extract_newsletter_industries
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reprocess_chief_ai_office_newsletters():
    """Reprocess Chief AI Office newsletters with updated link filters."""
    session = get_session()

    try:
        # Initialize database
        init_database()

        logger.info("="*80)
        logger.info("REPROCESSING CHIEF AI OFFICE NEWSLETTERS")
        logger.info("="*80)

        # Get all Chief AI Office newsletters
        newsletters = session.query(Newsletter).filter_by(
            source='Chief AI Office'
        ).order_by(Newsletter.id).all()

        if not newsletters:
            logger.warning("No Chief AI Office newsletters found in database")
            return

        total = len(newsletters)
        logger.info(f"Found {total} Chief AI Office newsletters to reprocess\n")

        updated_count = 0
        skipped_count = 0

        for i, newsletter in enumerate(newsletters, 1):
            try:
                logger.info(f"[{i}/{total}] Processing: {newsletter.title[:60]}...")

                # Re-extract links with new filters
                if newsletter.full_content:
                    old_link_count = len(newsletter.extracted_links) if newsletter.extracted_links else 0

                    new_links = extract_and_explain_links(
                        newsletter.full_content,
                        source='Chief AI Office'
                    )

                    new_link_count = len(new_links)

                    logger.info(f"  Links: {old_link_count} → {new_link_count} (removed {old_link_count - new_link_count} promotional links)")

                    # Update links
                    newsletter.extracted_links = new_links

                    # Regenerate summary with cleaned links
                    newsletter_data = {
                        'source': newsletter.source,
                        'email_subject': newsletter.email_subject or newsletter.title,
                        'html_content': newsletter.full_content,
                        'plain_text': newsletter.plain_text,
                        'extracted_links': new_links
                    }

                    old_summary = newsletter.summary
                    new_summary = generate_newsletter_summary(newsletter_data)
                    newsletter.summary = new_summary

                    # Regenerate tags
                    new_tags = extract_newsletter_tags(newsletter.title, new_summary)
                    newsletter.tags = new_tags

                    # Regenerate industries
                    new_industries = extract_newsletter_industries(newsletter.title, new_summary)
                    newsletter.industries = new_industries

                    logger.info(f"  Summary updated: {len(old_summary)} → {len(new_summary)} chars")
                    logger.info(f"  Tags: {newsletter.tags}")
                    logger.info(f"  Industries: {newsletter.industries}")

                    session.commit()
                    updated_count += 1
                    logger.info(f"  ✓ Updated successfully\n")
                else:
                    logger.info(f"  ⊘ Skipped (no content)\n")
                    skipped_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error: {e}\n")
                session.rollback()
                skipped_count += 1
                continue

        # Summary
        logger.info("="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total newsletters: {total}")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info("="*80 + "\n")

        if updated_count > 0:
            logger.info(f"✓ Successfully reprocessed {updated_count} Chief AI Office newsletters!")
            logger.info("  Promotional links have been removed and summaries regenerated.")
        else:
            logger.info("No newsletters were updated.")

    except Exception as e:
        logger.error(f"Error reprocessing newsletters: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    reprocess_chief_ai_office_newsletters()
