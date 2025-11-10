"""
Script to properly fix Chief AI Officer newsletter links.
Handles edge cases like companies named "Why".
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


def fix_chief_ai_merge():
    """
    Fix Chief AI Officer newsletter links with better logic.
    1. Rollback bad merges
    2. Re-extract and merge correctly
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get the specific newsletter with bad merges
        newsletter = session.query(Newsletter).filter(
            Newsletter.id == 175
        ).first()
        
        if not newsletter:
            logger.info("Newsletter 175 not found")
            return
        
        logger.info(f"Fixing Newsletter ID {newsletter.id}: {newsletter.title}")
        logger.info("\nCurrent links:")
        for i, link in enumerate(newsletter.extracted_links, 1):
            logger.info(f"  {i}. {link.get('title', 'No title')}")
        
        # Manual fix for this specific newsletter based on the pattern
        # We need to re-process from original HTML
        
        # For now, let's manually fix the known bad ones:
        fixed_links = []
        
        for link in newsletter.extracted_links:
            title = link.get('title', '')
            
            # Skip bad merges - we'll fix them manually
            if title in ['Why Felicis invested in Why', 'Why B Capital invested in Why']:
                continue
            
            # Fix "Axiom" to "Why Madrona invested in Axiom" (need to find the original)
            if title == 'Axiom':
                # This needs the "Why X invested" link which was consumed
                # Skip for now - we need to re-extract from HTML
                continue
                
            fixed_links.append(link)
        
        # Actually, let's re-extract from the original HTML
        from src.utils.link_extractor import extract_and_explain_links
        
        if newsletter.html_content:
            logger.info("\nRe-extracting links from original HTML...")
            new_links = extract_and_explain_links(
                newsletter.html_content,
                newsletter.source
            )
            
            logger.info(f"\nRe-extracted {len(new_links)} links:")
            for i, link in enumerate(new_links[:20], 1):
                logger.info(f"  {i}. {link.get('title', 'No title')}")
            
            # Now merge properly with better logic
            merged_links = []
            i = 0
            
            while i < len(new_links):
                current = new_links[i]
                current_title = current.get('title', '').strip()
                
                # Check if next link is "Why X invested"
                if i + 1 < len(new_links):
                    next_link = new_links[i + 1]
                    next_title = next_link.get('title', '').strip()
                    
                    # Pattern: current is company, next is "Why X invested"
                    why_match = re.match(r'Why (.+?) invested', next_title, re.IGNORECASE)
                    
                    if why_match and not current_title.lower().startswith('why'):
                        # Good merge: company name doesn't start with "Why"
                        investor = why_match.group(1)
                        
                        merged_link = {
                            'title': f'Why {investor} invested in {current_title}',
                            'url': next_link.get('url'),
                            'context': next_link.get('context', '')
                        }
                        
                        merged_links.append(merged_link)
                        i += 2  # Skip both
                        continue
                
                # No merge, keep as-is
                merged_links.append(current)
                i += 1
            
            logger.info(f"\n\nAfter proper merge - {len(merged_links)} links:")
            for i, link in enumerate(merged_links[:20], 1):
                logger.info(f"  {i}. {link.get('title', 'No title')}")
            
            # Update newsletter
            newsletter.extracted_links = merged_links
            session.commit()
            
            logger.info("\n✅ Fixed Newsletter 175!")
        else:
            logger.info("No HTML content available for re-extraction")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FIX CHIEF AI OFFICER MERGE")
    print("="*60 + "\n")
    
    fix_chief_ai_merge()

