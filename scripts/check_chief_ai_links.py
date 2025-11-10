"""
Script to check Chief AI Officer newsletter link patterns.
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


def check_chief_ai_links():
    """
    Check Chief AI Officer newsletter link patterns.
    """
    session = get_session()
    
    try:
        # Get Chief AI Officer newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%chief%ai%')
        ).all()
        
        if not newsletters:
            logger.info("No Chief AI Officer newsletters found")
            return
        
        logger.info(f"Found {len(newsletters)} Chief AI Officer newsletters\n")
        
        for newsletter in newsletters[:3]:  # Show first 3 for analysis
            logger.info(f"Newsletter ID {newsletter.id}: {newsletter.title}")
            logger.info(f"Source: {newsletter.source}")
            
            if newsletter.extracted_links:
                logger.info(f"Links ({len(newsletter.extracted_links)}):")
                for i, link in enumerate(newsletter.extracted_links[:10], 1):  # Show first 10 links
                    title = link.get('title', 'No title')
                    url = link.get('url', 'No URL')
                    logger.info(f"  {i}. {title}")
                    logger.info(f"     URL: {url[:80]}...")
            
            logger.info("")
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CHECK CHIEF AI OFFICER LINK PATTERNS")
    print("="*60 + "\n")
    
    check_chief_ai_links()


