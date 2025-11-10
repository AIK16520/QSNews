"""
Clean up ALL Chief AI Officer newsletters:
- Remove arrow prefixes (→)
- Filter out utility links
- Remove overly long descriptive titles
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


def cleanup_all_chief_ai():
    """
    Clean up all Chief AI Officer newsletters.
    """
    session = get_session()
    
    try:
        init_database()
        
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%chief%ai%')
        ).all()
        
        logger.info(f"Cleaning {len(newsletters)} Chief AI Officer newsletters...")
        
        updated_count = 0
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            original_count = len(newsletter.extracted_links)
            cleaned_links = []
            
            for link in newsletter.extracted_links:
                title = link.get('title', '').strip()
                
                # Remove arrow prefix
                if title.startswith('→ '):
                    title = title[2:].strip()
                    link['title'] = title
                
                # Filter out utility links
                utility_keywords = [
                    'Book a slot', 'Terms of use', 'Powered by beehiiv',
                    'Privacy policy', 'Unsubscribe', 'Manage subscription'
                ]
                
                if any(keyword.lower() in title.lower() for keyword in utility_keywords):
                    continue
                
                # Filter out overly long titles (likely articles, not companies)
                if len(title) > 100:
                    continue
                
                cleaned_links.append(link)
            
            removed = original_count - len(cleaned_links)
            
            if removed > 0:
                newsletter.extracted_links = cleaned_links
                updated_count += 1
                logger.info(f"  Newsletter ID {newsletter.id}: Removed {removed} links, {len(cleaned_links)} remaining")
        
        if updated_count > 0:
            session.commit()
            logger.info("="*60)
            logger.info(f"✅ Cleaned {updated_count} newsletters")
            logger.info("="*60)
        else:
            logger.info("✅ All newsletters already clean!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLEAN UP ALL CHIEF AI OFFICER NEWSLETTERS")
    print("="*60)
    print("\nThis will:")
    print("  - Remove arrow prefixes (→)")
    print("  - Filter out utility links")
    print("  - Remove overly long titles")
    print("="*60 + "\n")
    
    response = input("Clean up Chief AI Officer newsletters? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nCleaning...\n")
        cleanup_all_chief_ai()
        print("\n✅ Done!\n")
    else:
        print("\nCancelled.")


