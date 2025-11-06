#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to add 'industries' column to existing newsletters and extract industries using AI.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.database import get_session, Newsletter
from src.processors.newsletter_processor import extract_newsletter_industries
from sqlalchemy import inspect
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_industries_column():
    """Add industries column to newsletters table if it doesn't exist."""
    from sqlalchemy import text
    
    session = get_session()
    
    try:
        # Check if column exists
        inspector = inspect(session.bind)
        columns = [col['name'] for col in inspector.get_columns('newsletters')]
        
        if 'industries' in columns:
            logger.info("✓ 'industries' column already exists")
            return True
        
        logger.info("Adding 'industries' column to newsletters table...")
        
        # Add the column
        session.execute(text("ALTER TABLE newsletters ADD COLUMN industries JSON"))
        session.commit()
        
        logger.info("✓ Successfully added 'industries' column")
        return True
        
    except Exception as e:
        logger.error(f"Error adding column: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def extract_industries_for_newsletter(newsletter: Newsletter) -> bool:
    """Extract industries for a single newsletter."""
    try:
        if not newsletter.title:
            logger.warning(f"  Newsletter {newsletter.id} has no title, skipping")
            return False
        
        logger.info(f"Processing: {newsletter.source} - {newsletter.title[:60]}")
        
        # Extract industries
        industries = extract_newsletter_industries(newsletter.title, newsletter.summary or "")
        
        logger.info(f"  Extracted industries: {industries}")
        
        # Update the newsletter
        newsletter.industries = industries
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing newsletter {newsletter.id}: {e}")
        return False


def update_all_newsletters(batch_size: int = 10, dry_run: bool = False):
    """Extract industries for all newsletters."""
    session = get_session()
    
    try:
        # Get all newsletters
        newsletters = session.query(Newsletter).order_by(Newsletter.id).all()
        total = len(newsletters)
        
        logger.info("=" * 70)
        logger.info(f"EXTRACTING INDUSTRIES FOR NEWSLETTERS")
        logger.info(f"Total newsletters: {total}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 70)
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes will be saved\n")
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
            logger.error("Please set OPENAI_API_KEY to extract industries")
            logger.info("\nWill use keyword-based fallback extraction...")
        else:
            logger.info(f"✓ OpenAI API key found\n")
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, newsletter in enumerate(newsletters, 1):
            logger.info(f"\n[{i}/{total}] Processing newsletter ID {newsletter.id}")
            
            # Extract industries
            if extract_industries_for_newsletter(newsletter):
                updated_count += 1
                
                # Commit in batches (if not dry run)
                if not dry_run and updated_count % batch_size == 0:
                    session.commit()
                    logger.info(f"  ✓ Committed batch (total updated: {updated_count})")
            else:
                if newsletter.title:
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
        logger.info(f"Skipped (no title): {skipped_count}")
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add industries column and extract industries for newsletters')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without saving')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for commits (default: 10)')
    parser.add_argument('--skip-column', action='store_true', help='Skip adding column (if already added)')
    
    args = parser.parse_args()
    
    # Step 1: Add column if needed
    if not args.skip_column:
        logger.info("\nStep 1: Adding 'industries' column to database...")
        if not add_industries_column():
            logger.error("Failed to add column. Exiting.")
            sys.exit(1)
    else:
        logger.info("\nSkipping column addition (--skip-column flag set)")
    
    # Step 2: Extract industries
    logger.info("\nStep 2: Extracting industries for existing newsletters...\n")
    update_all_newsletters(batch_size=args.batch_size, dry_run=args.dry_run)


