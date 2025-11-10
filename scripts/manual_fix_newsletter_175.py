"""
Manually fix the bad merges in newsletter 175.
Based on the pattern, these should be:
- "Why" (company) + "Why Felicis invested" → "Why Felicis invested in Why"  
- "Axiom" (company) + "Why Madrona invested" (missing) → Need to add
- "Why" (company) + "Why B Capital invested" → "Why B Capital invested in Why"

Actually these ARE correct! The company is literally named "Why".
Let's just remove the arrow prefix from other links and filter better.
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


def manual_fix_175():
    """
    Fix newsletter 175 by removing arrow prefixes and filtering.
    """
    session = get_session()
    
    try:
        init_database()
        
        newsletter = session.query(Newsletter).filter(
            Newsletter.id == 175
        ).first()
        
        if not newsletter:
            logger.info("Newsletter 175 not found")
            return
        
        logger.info(f"Fixing Newsletter ID {newsletter.id}")
        logger.info("\nBefore:")
        for i, link in enumerate(newsletter.extracted_links, 1):
            logger.info(f"  {i}. {link.get('title', 'No title')}")
        
        # Clean up links
        cleaned_links = []
        
        for link in newsletter.extracted_links:
            title = link.get('title', '').strip()
            
            # Remove arrow prefix
            if title.startswith('→ '):
                title = title[2:].strip()
                link['title'] = title
            
            # Filter out utility links
            if title in ['Book a slot', 'Terms of use', 'Powered by beehiiv']:
                continue
            
            # Filter out long descriptive titles (likely articles, not companies)
            if len(title) > 80:
                continue
            
            cleaned_links.append(link)
        
        newsletter.extracted_links = cleaned_links
        session.commit()
        
        logger.info(f"\nAfter ({len(cleaned_links)} links):")
        for i, link in enumerate(cleaned_links, 1):
            logger.info(f"  {i}. {link.get('title', 'No title')}")
        
        logger.info("\n✅ Fixed newsletter 175!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MANUAL FIX NEWSLETTER 175")
    print("="*60 + "\n")
    
    manual_fix_175()

