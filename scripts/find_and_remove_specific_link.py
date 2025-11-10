"""
Find and remove a specific link from newsletters.
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


def find_and_remove_link(search_text):
    """
    Find and remove links containing specific text.
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get all newsletters with links
        newsletters = session.query(Newsletter).filter(
            Newsletter.extracted_links != None
        ).all()
        
        logger.info(f"Searching in {len(newsletters)} newsletters...")
        
        found_count = 0
        updated_newsletters = 0
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            original_count = len(newsletter.extracted_links)
            
            # Filter out links with the search text
            cleaned_links = []
            removed_in_this = 0
            
            for link in newsletter.extracted_links:
                title = link.get('title', '').strip()
                
                if search_text.lower() in title.lower():
                    logger.info(f"\nFound in Newsletter ID {newsletter.id} ({newsletter.source}):")
                    logger.info(f"  Title: '{title}'")
                    logger.info(f"  URL: {link.get('url', '')[:80]}...")
                    found_count += 1
                    removed_in_this += 1
                else:
                    cleaned_links.append(link)
            
            if removed_in_this > 0:
                newsletter.extracted_links = cleaned_links
                updated_newsletters += 1
                logger.info(f"  → Removed from this newsletter")
        
        if found_count > 0:
            logger.info(f"\n{'='*60}")
            logger.info(f"Found {found_count} links in {updated_newsletters} newsletters")
            logger.info(f"{'='*60}\n")
            
            response = input(f"Remove these {found_count} links? (yes/no): ").strip().lower()
            
            if response in ['yes', 'y']:
                session.commit()
                logger.info(f"✅ Removed {found_count} links from {updated_newsletters} newsletters!")
                return found_count, updated_newsletters
            else:
                logger.info("Removal cancelled")
                session.rollback()
                return 0, 0
        else:
            logger.info(f"✅ No links found containing '{search_text}'")
            return 0, 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 0, 0
    
    finally:
        session.close()


if __name__ == "__main__":
    search_text = "You can just read 25 books"
    
    print("\n" + "="*60)
    print("FIND AND REMOVE SPECIFIC LINK")
    print("="*60)
    print(f"\nSearching for: '{search_text}'")
    print("="*60 + "\n")
    
    removed, updated = find_and_remove_link(search_text)
    
    if removed > 0:
        print(f"\n✅ Done! Removed {removed} links from {updated} newsletters.\n")
    elif updated == 0 and removed == 0:
        print("\n✅ Link not found or already removed.\n")


