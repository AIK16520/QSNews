"""
Script to remove uninformative links from existing newsletters.
Removes links with generic titles like "Link", "launched", "debuted", etc.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from src.utils.database import get_session, Newsletter, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_uninformative_link(link):
    """
    Check if a link has an uninformative title.
    """
    title = link.get('title', '').strip().lower()
    
    # Generic/uninformative titles
    generic_titles = [
        'link', 'click here', 'read more', 'here', 
        'launched', 'debuted', 'unveiled', 'announced',
        'released', 'introducing', 'new', 'today',
        'more', 'details', 'learn more', 'see more'
    ]
    
    if title in generic_titles:
        return True
    
    # Very short titles
    if len(title) < 3:
        return True
    
    return False


def clean_newsletter_links():
    """
    Remove uninformative links from all newsletters.
    """
    session = get_session()
    
    try:
        # Initialize database
        init_database()
        
        # Get all newsletters with extracted links
        newsletters = session.query(Newsletter).filter(
            Newsletter.extracted_links != None
        ).all()
        
        logger.info(f"Checking {len(newsletters)} newsletters for uninformative links...")
        
        updated_count = 0
        total_removed = 0
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            original_count = len(newsletter.extracted_links)
            
            # Filter out uninformative links
            cleaned_links = [
                link for link in newsletter.extracted_links
                if not is_uninformative_link(link)
            ]
            
            removed_count = original_count - len(cleaned_links)
            
            if removed_count > 0:
                newsletter.extracted_links = cleaned_links
                updated_count += 1
                total_removed += removed_count
                logger.info(f"  Newsletter ID {newsletter.id} ({newsletter.source}): Removed {removed_count} uninformative links")
        
        if updated_count > 0:
            session.commit()
            logger.info("="*60)
            logger.info(f"✅ Cleaned {updated_count} newsletters")
            logger.info(f"✅ Removed {total_removed} uninformative links total")
            logger.info("="*60)
        else:
            logger.info("✅ No uninformative links found! All newsletters are clean.")
        
        return updated_count, total_removed
        
    except Exception as e:
        logger.error(f"Error cleaning links: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


def show_stats():
    """
    Show statistics about links.
    """
    session = get_session()
    
    try:
        newsletters = session.query(Newsletter).filter(
            Newsletter.extracted_links != None
        ).all()
        
        total_links = 0
        uninformative_links = 0
        
        for newsletter in newsletters:
            if newsletter.extracted_links:
                total_links += len(newsletter.extracted_links)
                for link in newsletter.extracted_links:
                    if is_uninformative_link(link):
                        uninformative_links += 1
        
        print("\n" + "="*60)
        print("LINK STATISTICS")
        print("="*60)
        print(f"Total newsletters:           {len(newsletters)}")
        print(f"Total links:                 {total_links}")
        print(f"Uninformative links:         {uninformative_links}")
        print(f"Good links:                  {total_links - uninformative_links}")
        print("="*60 + "\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLEAN UNINFORMATIVE LINKS FROM NEWSLETTERS")
    print("="*60)
    print("\nThis will remove links with generic titles like:")
    print("  - 'Link', 'launched', 'debuted', 'unveiled'")
    print("  - 'announced', 'released', 'click here', etc.")
    print("="*60 + "\n")
    
    # Show current stats
    show_stats()
    
    # Ask for confirmation
    response = input("Clean uninformative links? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nCleaning links...\n")
        updated, removed = clean_newsletter_links()
        
        if updated > 0:
            # Show updated stats
            show_stats()
            print(f"\n✅ Done! Cleaned {updated} newsletters, removed {removed} bad links.\n")
        else:
            print("\n✅ All newsletters are already clean!\n")
    else:
        print("\nCleaning cancelled.")


