"""
Database migration script to add Newsletter Builder fields.
Adds: commentary, newsletter_section, section_order to both articles and newsletters tables.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from sqlalchemy import text
from src.utils.database import get_session, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_add_builder_fields():
    """
    Add newsletter builder fields to articles and newsletters tables.
    """
    session = get_session()
    
    try:
        # Initialize database (creates tables if they don't exist)
        init_database()
        
        logger.info("Starting database migration...")
        
        # Check if columns already exist
        result = session.execute(text("PRAGMA table_info(articles)"))
        existing_columns = [row[1] for row in result]
        
        if 'commentary' in existing_columns:
            logger.info("✓ Migration already applied! Newsletter Builder fields exist.")
            return
        
        logger.info("Adding fields to articles table...")
        
        # Add fields to articles table
        session.execute(text("""
            ALTER TABLE articles 
            ADD COLUMN commentary TEXT
        """))
        logger.info("  ✓ Added articles.commentary")
        
        session.execute(text("""
            ALTER TABLE articles 
            ADD COLUMN newsletter_section TEXT
        """))
        logger.info("  ✓ Added articles.newsletter_section")
        
        session.execute(text("""
            ALTER TABLE articles 
            ADD COLUMN section_order INTEGER
        """))
        logger.info("  ✓ Added articles.section_order")
        
        logger.info("Adding fields to newsletters table...")
        
        # Add fields to newsletters table
        session.execute(text("""
            ALTER TABLE newsletters 
            ADD COLUMN commentary TEXT
        """))
        logger.info("  ✓ Added newsletters.commentary")
        
        session.execute(text("""
            ALTER TABLE newsletters 
            ADD COLUMN newsletter_section TEXT
        """))
        logger.info("  ✓ Added newsletters.newsletter_section")
        
        session.execute(text("""
            ALTER TABLE newsletters 
            ADD COLUMN section_order INTEGER
        """))
        logger.info("  ✓ Added newsletters.section_order")
        
        session.commit()
        
        logger.info("="*60)
        logger.info("✅ MIGRATION COMPLETE!")
        logger.info("Newsletter Builder fields added successfully.")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATABASE MIGRATION: Newsletter Builder Fields")
    print("="*60)
    print("\nThis will add the following fields:")
    print("  • commentary (user's manual notes)")
    print("  • newsletter_section (section assignment)")
    print("  • section_order (order in section)")
    print("\nTo both articles and newsletters tables.")
    print("="*60 + "\n")
    
    response = input("Run migration? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nRunning migration...\n")
        migrate_add_builder_fields()
        print("\n✅ Migration complete! You can now use Newsletter Builder.\n")
    else:
        print("\nMigration cancelled.")


