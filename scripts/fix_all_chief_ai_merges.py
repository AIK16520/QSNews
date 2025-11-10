"""
Fix ALL Chief AI Officer merges by reverting and re-merging with better logic.
Better logic: Don't merge if company name starts with "Why" (likely another investment link).
"""

import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from src.utils.database import get_session, Newsletter, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def un_merge_and_remerge_properly():
    """
    Un-merge bad Chief AI Officer links and re-merge with better logic.
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get all Chief AI Officer newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%chief%ai%')
        ).all()
        
        logger.info(f"Processing {len(newsletters)} Chief AI Officer newsletters...")
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            # Un-merge: split any "Why X invested in Y" back into parts
            unmerged_links = []
            
            for link in newsletter.extracted_links:
                title = link.get('title', '').strip()
                
                # Check if this is a merged link
                match = re.match(r'Why (.+?) invested in (.+)', title, re.IGNORECASE)
                
                if match:
                    investor = match.group(1)
                    company = match.group(2)
                    
                    # If company is "Why", this is a bad merge - keep only the investment link
                    if company == "Why":
                        # Just keep the "Why X invested" part without company
                        unmerged_links.append({
                            'title': f'Why {investor} invested',
                            'url': link.get('url'),
                            'context': link.get('context', '')
                        })
                    else:
                        # Good merge, keep it
                        unmerged_links.append(link)
                else:
                    # Not a merged link, keep as-is
                    unmerged_links.append(link)
            
            # Update the newsletter
            newsletter.extracted_links = unmerged_links
            
        session.commit()
        logger.info("✅ Fixed all Chief AI Officer newsletters!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()


def show_newsletter_175():
    """Show newsletter 175 after fix."""
    session = get_session()
    
    try:
        newsletter = session.query(Newsletter).filter(
            Newsletter.id == 175
        ).first()
        
        if newsletter:
            print("\n" + "="*60)
            print(f"Newsletter 175 - After Fix:")
            print("="*60)
            for i, link in enumerate(newsletter.extracted_links[:12], 1):
                print(f"{i}. {link.get('title', 'No title')}")
            print("="*60 + "\n")
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FIX CHIEF AI OFFICER MERGES")
    print("="*60)
    print("\nThis will fix bad merges like:")
    print("  'Why X invested in Why' → 'Why X invested'")
    print("="*60 + "\n")
    
    response = input("Fix Chief AI Officer links? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nFixing...\n")
        un_merge_and_remerge_properly()
        show_newsletter_175()
        print("✅ Done!\n")
    else:
        print("\nCancelled.")


