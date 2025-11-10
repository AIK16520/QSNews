"""
Script to find the bad merge in Chief AI Officer newsletter.
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


def check_bad_merges():
    """
    Find newsletters with the bad "Why X invested in Why" pattern.
    """
    session = get_session()
    
    try:
        # Get Chief AI Officer newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%chief%ai%')
        ).all()
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            # Look for the bad pattern
            for link in newsletter.extracted_links:
                title = link.get('title', '')
                if 'invested in Why' in title or title == 'Axiom' or 'invested in MAI' in title:
                    logger.info(f"\nNewsletter ID {newsletter.id}: {newsletter.title}")
                    logger.info(f"Published: {newsletter.published_date}")
                    logger.info("All links:")
                    for i, l in enumerate(newsletter.extracted_links, 1):
                        logger.info(f"  {i}. {l.get('title', 'No title')}")
                    break
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CHECK BAD MERGES")
    print("="*60 + "\n")
    
    check_bad_merges()


