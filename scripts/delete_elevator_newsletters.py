"""
Script to delete all Elevator newsletters from the database.
Removes newsletters from 'Gettheelevator' or containing elevator tracking links.
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


def delete_elevator_newsletters():
    """
    Delete all Elevator newsletters from database.
    """
    session = get_session()
    
    try:
        # Initialize database
        init_database()
        
        # Find all Elevator newsletters
        elevator_patterns = [
            'Gettheelevator',
            'The Elevator',
            'Elevator'
        ]
        
        elevator_newsletters = []
        
        # Search by source
        for pattern in elevator_patterns:
            newsletters = session.query(Newsletter).filter(
                Newsletter.source.ilike(f'%{pattern}%')
            ).all()
            elevator_newsletters.extend(newsletters)
        
        # Also find newsletters with elevator tracking links
        all_newsletters = session.query(Newsletter).all()
        for newsletter in all_newsletters:
            if newsletter.extracted_links:
                for link in newsletter.extracted_links:
                    url = link.get('url', '').lower()
                    if 'elevator' in url or 'gettheelevator' in url:
                        if newsletter not in elevator_newsletters:
                            elevator_newsletters.append(newsletter)
                        break
        
        # Remove duplicates
        elevator_newsletters = list(set(elevator_newsletters))
        
        if not elevator_newsletters:
            logger.info("No Elevator newsletters found in database!")
            return 0
        
        logger.info(f"Found {len(elevator_newsletters)} Elevator newsletters to delete:")
        for newsletter in elevator_newsletters:
            logger.info(f"  - ID: {newsletter.id}, Source: {newsletter.source}, Title: {newsletter.title[:60]}...")
        
        # Ask for confirmation
        print("\n" + "="*60)
        response = input(f"Delete {len(elevator_newsletters)} Elevator newsletters? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            logger.info("Deletion cancelled.")
            return 0
        
        # Delete newsletters
        deleted_count = 0
        for newsletter in elevator_newsletters:
            session.delete(newsletter)
            deleted_count += 1
            logger.info(f"Deleted: {newsletter.source} - {newsletter.title[:60]}")
        
        session.commit()
        
        logger.info("="*60)
        logger.info(f"✅ Successfully deleted {deleted_count} Elevator newsletters!")
        logger.info("="*60)
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error deleting newsletters: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


def show_elevator_stats():
    """
    Show statistics about Elevator newsletters.
    """
    session = get_session()
    
    try:
        total_newsletters = session.query(Newsletter).count()
        
        # Count elevator newsletters
        elevator_count = session.query(Newsletter).filter(
            Newsletter.source.ilike('%Elevator%')
        ).count()
        
        print("\n" + "="*60)
        print("ELEVATOR NEWSLETTER STATISTICS")
        print("="*60)
        print(f"Total newsletters:       {total_newsletters}")
        print(f"Elevator newsletters:    {elevator_count}")
        print(f"Other newsletters:       {total_newsletters - elevator_count}")
        print("="*60 + "\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DELETE ELEVATOR NEWSLETTERS")
    print("="*60)
    
    # Show current stats
    show_elevator_stats()
    
    # Delete Elevator newsletters
    deleted = delete_elevator_newsletters()
    
    if deleted > 0:
        # Show updated stats
        show_elevator_stats()
        print(f"\n✅ Done! Deleted {deleted} Elevator newsletters.\n")


