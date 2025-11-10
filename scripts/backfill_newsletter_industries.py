"""
Script to backfill industries for existing newsletters that don't have them.
Runs the extract_newsletter_industries function on all newsletters without industries.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from src.utils.database import get_session, Newsletter, init_database
from src.processors.newsletter_processor import extract_newsletter_industries

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_newsletter_industries():
    """
    Update existing newsletters that don't have industries assigned.
    """
    session = get_session()
    
    try:
        # Initialize database
        init_database()
        
        # Get all newsletters without industries
        newsletters = session.query(Newsletter).filter(
            (Newsletter.industries == None) | (Newsletter.industries == [])
        ).all()
        
        if not newsletters:
            logger.info("No newsletters need industry backfill. All newsletters have industries assigned!")
            return 0
        
        logger.info(f"Found {len(newsletters)} newsletters without industries. Starting backfill...")
        
        updated_count = 0
        error_count = 0
        
        for i, newsletter in enumerate(newsletters, 1):
            try:
                # Extract industries using AI
                logger.info(f"[{i}/{len(newsletters)}] Processing: {newsletter.source} - {newsletter.title[:60]}...")
                
                industries = extract_newsletter_industries(
                    title=newsletter.title,
                    summary=newsletter.summary or ""
                )
                
                # Update newsletter
                newsletter.industries = industries
                session.commit()
                
                updated_count += 1
                logger.info(f"  ✓ Assigned industries: {industries}")
                
            except Exception as e:
                logger.error(f"  ✗ Error processing newsletter {newsletter.id}: {e}")
                session.rollback()
                error_count += 1
                continue
        
        logger.info("="*80)
        logger.info("BACKFILL COMPLETE")
        logger.info(f"  Updated: {updated_count} newsletters")
        logger.info(f"  Errors: {error_count}")
        logger.info("="*80)
        
        return updated_count
        
    except Exception as e:
        logger.error(f"Fatal error during backfill: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


def show_newsletter_stats():
    """
    Display statistics about newsletter industries.
    """
    session = get_session()
    
    try:
        total = session.query(Newsletter).count()
        with_industries = session.query(Newsletter).filter(
            Newsletter.industries != None,
            Newsletter.industries != []
        ).count()
        without_industries = total - with_industries
        
        print("\n" + "="*60)
        print("NEWSLETTER INDUSTRY STATISTICS")
        print("="*60)
        print(f"Total newsletters:       {total}")
        print(f"With industries:         {with_industries}")
        print(f"Without industries:      {without_industries}")
        print("="*60 + "\n")
        
        if without_industries > 0:
            print(f"Run backfill to assign industries to {without_industries} newsletters.\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("NEWSLETTER INDUSTRIES BACKFILL SCRIPT")
    print("="*80)
    
    # Show current stats
    show_newsletter_stats()
    
    # Ask for confirmation
    response = input("Do you want to backfill industries for newsletters? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nStarting backfill...\n")
        updated = backfill_newsletter_industries()
        
        print(f"\n✅ Backfill complete! Updated {updated} newsletters.")
        
        # Show updated stats
        show_newsletter_stats()
    else:
        print("\nBackfill cancelled.")


