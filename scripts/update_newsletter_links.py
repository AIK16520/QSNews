#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to update existing newsletters with improved link extraction.
Re-processes HTML content to extract better link context and filter out utility links.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.database import get_session, Newsletter
from src.utils.link_extractor import extract_and_explain_links
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_single_newsletter(newsletter: Newsletter) -> bool:
    """
    Update a single newsletter's link data.
    
    Args:
        newsletter: Newsletter object to update
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        logger.info(f"Processing: {newsletter.source} - {newsletter.title[:60]}")
        
        # Check if we have HTML content
        if not newsletter.full_content:
            logger.warning("  No HTML content available, skipping")
            return False
        
        # Extract links with new logic
        new_links = extract_and_explain_links(
            newsletter.full_content,
            source=newsletter.source
        )
        
        # Count before/after
        old_count = len(newsletter.extracted_links) if newsletter.extracted_links else 0
        new_count = len(new_links)
        
        logger.info(f"  Links: {old_count} -> {new_count} (filtered {old_count - new_count})")
        
        # Update the newsletter
        newsletter.extracted_links = new_links
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating newsletter {newsletter.id}: {e}")
        return False


def update_all_newsletters(batch_size: int = 10, dry_run: bool = False):
    """
    Update all newsletters in the database with better link extraction.
    
    Args:
        batch_size: Number of newsletters to commit at once
        dry_run: If True, don't commit changes (just show what would happen)
    """
    session = get_session()
    
    try:
        # Get all newsletters
        newsletters = session.query(Newsletter).order_by(Newsletter.id).all()
        total = len(newsletters)
        
        logger.info("=" * 70)
        logger.info(f"UPDATING NEWSLETTER LINKS")
        logger.info(f"Total newsletters: {total}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 70)
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes will be saved\n")
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, newsletter in enumerate(newsletters, 1):
            logger.info(f"\n[{i}/{total}] Processing newsletter ID {newsletter.id}")
            
            # Update the newsletter
            if update_single_newsletter(newsletter):
                updated_count += 1
                
                # Commit in batches (if not dry run)
                if not dry_run and updated_count % batch_size == 0:
                    session.commit()
                    logger.info(f"  ✓ Committed batch (total updated: {updated_count})")
            else:
                if newsletter.full_content:
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


def update_specific_newsletters(newsletter_ids: list, dry_run: bool = False):
    """
    Update specific newsletters by ID.
    
    Args:
        newsletter_ids: List of newsletter IDs to update
        dry_run: If True, don't commit changes
    """
    session = get_session()
    
    try:
        logger.info("=" * 70)
        logger.info(f"UPDATING SPECIFIC NEWSLETTERS")
        logger.info(f"IDs: {newsletter_ids}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 70)
        
        updated_count = 0
        
        for newsletter_id in newsletter_ids:
            newsletter = session.query(Newsletter).filter_by(id=newsletter_id).first()
            
            if not newsletter:
                logger.warning(f"Newsletter ID {newsletter_id} not found")
                continue
            
            logger.info(f"\nProcessing newsletter ID {newsletter_id}")
            
            if update_single_newsletter(newsletter):
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
    Show a before/after comparison for a newsletter.
    
    Args:
        newsletter_id: Specific newsletter ID, or None for first newsletter
    """
    session = get_session()
    
    try:
        if newsletter_id:
            newsletter = session.query(Newsletter).filter_by(id=newsletter_id).first()
        else:
            newsletter = session.query(Newsletter).first()
        
        if not newsletter:
            logger.error("No newsletter found")
            return
        
        logger.info("=" * 70)
        logger.info("BEFORE/AFTER COMPARISON")
        logger.info("=" * 70)
        logger.info(f"Newsletter: {newsletter.source} - {newsletter.title[:60]}")
        logger.info("")
        
        # Show current links
        logger.info("CURRENT LINKS (in database):")
        logger.info("-" * 70)
        current_links = newsletter.extracted_links if newsletter.extracted_links else []
        for i, link in enumerate(current_links[:10], 1):  # Show first 10
            logger.info(f"{i}. {link.get('title', 'Untitled')}")
            logger.info(f"   URL: {link.get('url', '')}")
            logger.info(f"   Context: {link.get('context', '(none)')}")
            logger.info("")
        
        if len(current_links) > 10:
            logger.info(f"... and {len(current_links) - 10} more links")
        logger.info(f"Total current links: {len(current_links)}")
        
        # Generate new links (without saving)
        logger.info("\n" + "=" * 70)
        logger.info("NEW LINKS (after update):")
        logger.info("-" * 70)
        
        if newsletter.full_content:
            new_links = extract_and_explain_links(
                newsletter.full_content,
                source=newsletter.source
            )
            
            for i, link in enumerate(new_links[:10], 1):  # Show first 10
                logger.info(f"{i}. {link.get('title', 'Untitled')}")
                logger.info(f"   URL: {link.get('url', '')}")
                logger.info(f"   Explanation: {link.get('explanation', '(none)')}")
                logger.info(f"   Domain: {link.get('domain', '')}")
                logger.info("")
            
            if len(new_links) > 10:
                logger.info(f"... and {len(new_links) - 10} more links")
            logger.info(f"Total new links: {len(new_links)}")
            
            # Stats
            logger.info("\n" + "=" * 70)
            logger.info("STATISTICS:")
            logger.info(f"Before: {len(current_links)} links")
            logger.info(f"After: {len(new_links)} links")
            logger.info(f"Filtered: {len(current_links) - len(new_links)} links")
            logger.info(f"Reduction: {((len(current_links) - len(new_links)) / len(current_links) * 100):.1f}%")
        else:
            logger.info("No HTML content available for this newsletter")
        
        logger.info("=" * 70)
        
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update newsletter links with better extraction')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without saving')
    parser.add_argument('--ids', type=str, help='Comma-separated list of newsletter IDs to update')
    parser.add_argument('--sample', action='store_true', help='Show before/after sample for one newsletter')
    parser.add_argument('--sample-id', type=int, help='Newsletter ID for sample comparison')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for commits (default: 10)')
    
    args = parser.parse_args()
    
    if args.sample:
        # Show sample comparison
        show_before_after_sample(newsletter_id=args.sample_id)
    
    elif args.ids:
        # Update specific newsletters
        newsletter_ids = [int(id.strip()) for id in args.ids.split(',')]
        update_specific_newsletters(newsletter_ids, dry_run=args.dry_run)
    
    else:
        # Update all newsletters
        update_all_newsletters(batch_size=args.batch_size, dry_run=args.dry_run)


