"""
Remove promotional and administrative links from TLDR newsletters.
Includes: View Online, Sign Up, Advertise, Sponsor, Enterprise-grade, etc.
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


def is_promo_link(link):
    """
    Check if a link is promotional/administrative.
    """
    title = link.get('title', '').strip().lower()
    url = link.get('url', '').lower()
    
    unwanted_patterns = [
        # Sponsored/Ads
        'sponsor', 'sponsored', '(sponsor)', 'advertisement', 'advertise',
        
        # Sign up / Newsletter management
        'sign up', 'signup', 'subscribe', 'unsubscribe',
        'manage your subscriptions', 'manage subscriptions',
        
        # View/Share links
        'view online', 'view in browser', 'read online', 'web version',
        
        # Common marketing/promo
        'enterprise-grade', 'enterprising solutions',
    ]
    
    for pattern in unwanted_patterns:
        if pattern in title or pattern in url:
            return True
    
    return False


def clean_tldr_links():
    """
    Remove promotional links from TLDR newsletters.
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get TLDR newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%tldr%')
        ).all()
        
        logger.info(f"Checking {len(newsletters)} TLDR newsletters...")
        
        updated_count = 0
        total_removed = 0
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            original_count = len(newsletter.extracted_links)
            
            # Filter out promo links
            cleaned_links = [
                link for link in newsletter.extracted_links
                if not is_promo_link(link)
            ]
            
            removed = original_count - len(cleaned_links)
            
            if removed > 0:
                newsletter.extracted_links = cleaned_links
                updated_count += 1
                total_removed += removed
                logger.info(f"  Newsletter ID {newsletter.id}: Removed {removed} promo links, {len(cleaned_links)} remaining")
        
        if updated_count > 0:
            session.commit()
            logger.info("="*60)
            logger.info(f"✅ Cleaned {updated_count} newsletters")
            logger.info(f"✅ Removed {total_removed} promotional links")
            logger.info("="*60)
            return updated_count, total_removed
        else:
            logger.info("✅ No promotional links found! All newsletters are clean.")
            return 0, 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 0, 0
    
    finally:
        session.close()


def show_example():
    """Show example of what will be removed."""
    session = get_session()
    
    try:
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%tldr%')
        ).limit(1).all()
        
        if newsletters and newsletters[0].extracted_links:
            print("\n" + "="*60)
            print("EXAMPLE - What will be removed:")
            print("="*60)
            
            count = 0
            for link in newsletters[0].extracted_links[:15]:
                title = link.get('title', '')
                if is_promo_link(link):
                    print(f"  ❌ '{title}'")
                    count += 1
                    if count >= 5:
                        break
            
            if count == 0:
                print("  No promotional links found in sample")
            
            print("="*60 + "\n")
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLEAN TLDR PROMOTIONAL LINKS")
    print("="*60)
    print("\nThis will remove:")
    print("  - View Online, Sign Up, Advertise")
    print("  - Sponsor, Enterprise-grade")
    print("  - Subscribe, Unsubscribe")
    print("="*60 + "\n")
    
    show_example()
    
    response = input("Clean TLDR promotional links? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nCleaning...\n")
        updated, removed = clean_tldr_links()
        
        if updated > 0:
            print(f"\n✅ Done! Cleaned {updated} newsletters, removed {removed} promo links.\n")
        else:
            print("\n✅ All newsletters are already clean!\n")
    else:
        print("\nCancelled.")


