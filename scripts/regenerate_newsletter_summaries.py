#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to regenerate summaries for existing newsletters.
Uses the updated prompt that excludes emojis.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.database import get_session, Newsletter
from src.processors.newsletter_processor import generate_newsletter_summary
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def regenerate_single_newsletter_summary(newsletter: Newsletter) -> bool:
    """
    Regenerate summary for a single newsletter.
    
    Args:
        newsletter: Newsletter object to update
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        logger.info(f"Processing: {newsletter.source} - {newsletter.title[:60]}")
        
        # Check if we have content
        if not newsletter.full_content and not newsletter.plain_text:
            logger.warning("  No content available, skipping")
            return False
        
        # Build newsletter data dict for summary generation
        newsletter_data = {
            'source': newsletter.source,
            'email_subject': newsletter.email_subject or newsletter.title,
            'html_content': newsletter.full_content,
            'plain_text': newsletter.plain_text,
            'extracted_links': newsletter.extracted_links if newsletter.extracted_links else []
        }
        
        # Generate new summary
        old_summary = newsletter.summary
        new_summary = generate_newsletter_summary(newsletter_data)
        
        logger.info(f"  Old: {old_summary[:80]}...")
        logger.info(f"  New: {new_summary[:80]}...")
        
        # Update the newsletter
        newsletter.summary = new_summary
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating newsletter {newsletter.id}: {e}")
        return False


def regenerate_all_summaries(batch_size: int = 10, dry_run: bool = False):
    """
    Regenerate summaries for all newsletters in the database.
    
    Args:
        batch_size: Number of newsletters to commit at once
        dry_run: If True, don't commit changes (just show what would happen)
    """
    session = get_session()
    
    try:
        # Get all newsletters that have content
        newsletters = session.query(Newsletter).filter(
            (Newsletter.full_content != None) | (Newsletter.plain_text != None)
        ).order_by(Newsletter.id).all()
        
        total = len(newsletters)
        
        logger.info("=" * 70)
        logger.info(f"REGENERATING NEWSLETTER SUMMARIES")
        logger.info(f"Total newsletters with content: {total}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 70)
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes will be saved\n")
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
            logger.error("Please set OPENAI_API_KEY to regenerate summaries")
            return
        
        logger.info(f"✓ OpenAI API key found\n")
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, newsletter in enumerate(newsletters, 1):
            logger.info(f"\n[{i}/{total}] Processing newsletter ID {newsletter.id}")
            
            # Regenerate the summary
            if regenerate_single_newsletter_summary(newsletter):
                updated_count += 1
                
                # Commit in batches (if not dry run)
                if not dry_run and updated_count % batch_size == 0:
                    session.commit()
                    logger.info(f"  ✓ Committed batch (total updated: {updated_count})")
            else:
                if newsletter.full_content or newsletter.plain_text:
                    failed_count += 1
                else:
                    skipped_count += 1
        
        # Final commit (if not dry run)
        if not dry_run and updated_count > 0:
            session.commit()
            logger.info(f"\n✓ Final commit complete")
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("UPDATE SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total newsletters: {total}")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Skipped (no content): {skipped_count}")
        logger.info(f"Failed: {failed_count}")
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN - No changes were saved to database")
            logger.info("Run without --dry-run to actually update the database")
        else:
            logger.info("\n✓ All changes saved to database")
        
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error in batch update: {e}")
        if not dry_run:
            session.rollback()
            logger.info("Rolled back changes due to error")
    
    finally:
        session.close()


def regenerate_specific_summaries(newsletter_ids: list, dry_run: bool = False):
    """
    Regenerate summaries for specific newsletters by ID.
    
    Args:
        newsletter_ids: List of newsletter IDs to update
        dry_run: If True, don't commit changes
    """
    session = get_session()
    
    try:
        logger.info("=" * 70)
        logger.info(f"REGENERATING SPECIFIC NEWSLETTER SUMMARIES")
        logger.info(f"IDs: {newsletter_ids}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 70)
        
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
            return
        
        updated_count = 0
        
        for newsletter_id in newsletter_ids:
            newsletter = session.query(Newsletter).filter_by(id=newsletter_id).first()
            
            if not newsletter:
                logger.warning(f"Newsletter ID {newsletter_id} not found")
                continue
            
            logger.info(f"\nProcessing newsletter ID {newsletter_id}")
            
            if regenerate_single_newsletter_summary(newsletter):
                updated_count += 1
        
        # Commit changes
        if not dry_run and updated_count > 0:
            session.commit()
            logger.info(f"\n✓ Updated and committed {updated_count} newsletters")
        else:
            logger.info(f"\n⚠️  DRY RUN - Would have updated {updated_count} newsletters")
        
    except Exception as e:
        logger.error(f"Error updating specific newsletters: {e}")
        if not dry_run:
            session.rollback()
    
    finally:
        session.close()


def show_before_after_sample(newsletter_id: int = None):
    """
    Show a before/after comparison for a newsletter summary.
    
    Args:
        newsletter_id: Specific newsletter ID, or None for first newsletter
    """
    session = get_session()
    
    try:
        if newsletter_id:
            newsletter = session.query(Newsletter).filter_by(id=newsletter_id).first()
        else:
            newsletter = session.query(Newsletter).filter(
                (Newsletter.full_content != None) | (Newsletter.plain_text != None)
            ).first()
        
        if not newsletter:
            logger.error("No newsletter found")
            return
        
        logger.info("=" * 70)
        logger.info("BEFORE/AFTER COMPARISON - SUMMARY REGENERATION")
        logger.info("=" * 70)
        logger.info(f"Newsletter: {newsletter.source} - {newsletter.title[:60]}")
        logger.info("")
        
        # Show current summary
        logger.info("CURRENT SUMMARY (in database):")
        logger.info("-" * 70)
        logger.info(newsletter.summary if newsletter.summary else "(no summary)")
        logger.info("")
        
        # Generate new summary (without saving)
        logger.info("NEW SUMMARY (after regeneration):")
        logger.info("-" * 70)
        
        if newsletter.full_content or newsletter.plain_text:
            newsletter_data = {
                'source': newsletter.source,
                'email_subject': newsletter.email_subject or newsletter.title,
                'html_content': newsletter.full_content,
                'plain_text': newsletter.plain_text,
                'extracted_links': newsletter.extracted_links if newsletter.extracted_links else []
            }
            
            new_summary = generate_newsletter_summary(newsletter_data)
            logger.info(new_summary)
        else:
            logger.info("No content available for this newsletter")
        
        logger.info("")
        logger.info("=" * 70)
        
    finally:
        session.close()


def count_newsletters_with_emojis():
    """Count how many newsletters have emojis in their summaries."""
    session = get_session()
    
    try:
        import re
        
        newsletters = session.query(Newsletter).filter(
            Newsletter.summary != None
        ).all()
        
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        
        with_emojis = []
        for newsletter in newsletters:
            if newsletter.summary and emoji_pattern.search(newsletter.summary):
                with_emojis.append(newsletter)
        
        logger.info("=" * 70)
        logger.info("EMOJI COUNT IN SUMMARIES")
        logger.info("=" * 70)
        logger.info(f"Total newsletters with summaries: {len(newsletters)}")
        logger.info(f"Newsletters with emojis: {len(with_emojis)}")
        logger.info(f"Percentage: {len(with_emojis) / len(newsletters) * 100:.1f}%")
        
        if with_emojis:
            logger.info("\nExamples with emojis:")
            for i, nl in enumerate(with_emojis[:5], 1):
                logger.info(f"\n{i}. {nl.source} (ID: {nl.id})")
                logger.info(f"   {nl.summary[:100]}...")
        
        logger.info("=" * 70)
        
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Regenerate newsletter summaries with updated prompt')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without saving')
    parser.add_argument('--ids', type=str, help='Comma-separated list of newsletter IDs to update')
    parser.add_argument('--sample', action='store_true', help='Show before/after sample for one newsletter')
    parser.add_argument('--sample-id', type=int, help='Newsletter ID for sample comparison')
    parser.add_argument('--count-emojis', action='store_true', help='Count newsletters with emojis')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for commits (default: 10)')
    
    args = parser.parse_args()
    
    if args.count_emojis:
        # Count how many have emojis
        count_newsletters_with_emojis()
    
    elif args.sample:
        # Show sample comparison
        show_before_after_sample(newsletter_id=args.sample_id)
    
    elif args.ids:
        # Update specific newsletters
        newsletter_ids = [int(id.strip()) for id in args.ids.split(',')]
        regenerate_specific_summaries(newsletter_ids, dry_run=args.dry_run)
    
    else:
        # Update all newsletters
        regenerate_all_summaries(batch_size=args.batch_size, dry_run=args.dry_run)


