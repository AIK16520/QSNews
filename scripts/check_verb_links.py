"""
Check links with verb-only titles and their available context.
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


def check_verb_links():
    """
    Find links with verb-only titles.
    """
    session = get_session()
    
    try:
        # Get The Rundown newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%rundown%')
        ).all()
        
        verb_titles = ['pulling', 'told', 'developed', 'come', 'building', 
                      'secured', 'reports', 'said', 'raised', 'announced',
                      'launched', 'unveiled', 'released', 'introducing']
        
        logger.info(f"Checking {len(newsletters)} Rundown newsletters...")
        
        found_count = 0
        
        for newsletter in newsletters[:3]:  # Check first 3
            if not newsletter.extracted_links:
                continue
            
            for link in newsletter.extracted_links:
                title = link.get('title', '').strip().lower()
                
                if title in verb_titles:
                    found_count += 1
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Newsletter ID {newsletter.id}")
                    logger.info(f"Title: '{link.get('title', '')}'")
                    logger.info(f"URL: {link.get('url', '')[:80]}...")
                    logger.info(f"Context: {link.get('context', 'NO CONTEXT')[:200]}...")
                    
                    if found_count >= 5:
                        logger.info(f"\n{'='*60}")
                        logger.info("Showing first 5 examples only")
                        return
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CHECK VERB-ONLY LINKS")
    print("="*60 + "\n")
    
    check_verb_links()


