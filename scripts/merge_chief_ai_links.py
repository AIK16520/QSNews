"""
Script to merge Chief AI Officer newsletter links.
Combines company name + "Why X invested" into one descriptive link.
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


def merge_chief_ai_links():
    """
    Merge Chief AI Officer newsletter links.
    Pattern: "Company Name" + "Why X invested" → "Why X invested in Company Name"
    """
    session = get_session()
    
    try:
        # Initialize database
        init_database()
        
        # Get Chief AI Officer newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%chief%ai%')
        ).all()
        
        if not newsletters:
            logger.info("No Chief AI Officer newsletters found")
            return 0
        
        logger.info(f"Processing {len(newsletters)} Chief AI Officer newsletters...")
        
        updated_count = 0
        total_merged = 0
        
        for newsletter in newsletters:
            if not newsletter.extracted_links or len(newsletter.extracted_links) < 2:
                continue
            
            merged_links = []
            i = 0
            merged_in_newsletter = 0
            
            while i < len(newsletter.extracted_links):
                current_link = newsletter.extracted_links[i]
                current_title = current_link.get('title', '').strip()
                
                # Check if next link is a "Why X invested" link
                if i + 1 < len(newsletter.extracted_links):
                    next_link = newsletter.extracted_links[i + 1]
                    next_title = next_link.get('title', '').strip()
                    
                    # Match pattern: "Why [Investor] invested"
                    if re.match(r'Why .+ invested', next_title, re.IGNORECASE):
                        # This is the pattern! Merge them
                        company_name = current_title
                        
                        # Extract investor name from "Why X invested"
                        investor_match = re.search(r'Why (.+?) invested', next_title, re.IGNORECASE)
                        if investor_match:
                            investor = investor_match.group(1)
                            
                            # Create merged link with descriptive title
                            merged_link = {
                                'title': f'Why {investor} invested in {company_name}',
                                'url': next_link.get('url'),  # Keep the analysis URL
                                'context': next_link.get('context', '')
                            }
                            
                            merged_links.append(merged_link)
                            merged_in_newsletter += 1
                            
                            # Skip both links (current company + next why)
                            i += 2
                            continue
                
                # No merge pattern found, keep the link as-is
                merged_links.append(current_link)
                i += 1
            
            # Update newsletter if we merged any links
            if merged_in_newsletter > 0:
                newsletter.extracted_links = merged_links
                updated_count += 1
                total_merged += merged_in_newsletter
                logger.info(f"  Newsletter ID {newsletter.id}: Merged {merged_in_newsletter} link pairs")
        
        if updated_count > 0:
            session.commit()
            logger.info("="*60)
            logger.info(f"✅ Updated {updated_count} newsletters")
            logger.info(f"✅ Merged {total_merged} link pairs")
            logger.info("="*60)
        else:
            logger.info("✅ No links to merge! All newsletters are already clean.")
        
        return updated_count, total_merged
        
    except Exception as e:
        logger.error(f"Error merging links: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


def show_before_after():
    """
    Show before/after examples.
    """
    session = get_session()
    
    try:
        newsletters = session.query(Newsletter).filter(
            Newsletter.source.ilike('%chief%ai%')
        ).limit(1).all()
        
        if newsletters:
            newsletter = newsletters[0]
            print("\n" + "="*60)
            print("EXAMPLE - BEFORE MERGE:")
            print("="*60)
            if newsletter.extracted_links:
                for i, link in enumerate(newsletter.extracted_links[:6], 1):
                    print(f"{i}. {link.get('title', 'No title')}")
            print("="*60 + "\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MERGE CHIEF AI OFFICER LINKS")
    print("="*60)
    print("\nThis will merge:")
    print("  'Company Name' + 'Why X invested'")
    print("  → 'Why X invested in Company Name'")
    print("="*60 + "\n")
    
    # Show example before
    show_before_after()
    
    # Ask for confirmation
    response = input("Merge Chief AI Officer links? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nMerging links...\n")
        updated, merged = merge_chief_ai_links()
        
        if updated > 0:
            print(f"\n✅ Done! Updated {updated} newsletters, merged {merged} link pairs.\n")
            
            # Show example after
            show_before_after()
        else:
            print("\n✅ All newsletters are already clean!\n")
    else:
        print("\nMerging cancelled.")


