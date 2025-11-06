#!/usr/bin/env python3
"""
Check database content for generated articles
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.utils.database import get_session, Article

def check_database_content():
    """Check what's actually stored in the database."""
    print("🔍 Checking Database Content")
    print("=" * 50)
    
    session = get_session()
    
    try:
        # Get all articles
        articles = session.query(Article).all()
        print(f"📊 Total articles in database: {len(articles)}")
        
        # Check by status
        statuses = ['included', 'in_review', 'generated', 'finalized', 'not_included']
        for status in statuses:
            count = session.query(Article).filter_by(status=status).count()
            print(f"  - {status}: {count} articles")
        
        print("\n📰 Articles with 'generated' status:")
        generated_articles = session.query(Article).filter_by(status='generated').all()
        
        for i, article in enumerate(generated_articles):
            print(f"\n--- Article {i+1} ---")
            print(f"Title: {article.title}")
            print(f"Status: {article.status}")
            print(f"Generated Content Length: {len(article.generated_content) if article.generated_content else 0}")
            print(f"Final Content Length: {len(article.final_content) if article.final_content else 0}")
            print(f"User Content Length: {len(article.user_content) if article.user_content else 0}")
            print(f"AI Instructions: {article.ai_instructions}")
            
            if article.generated_content:
                print(f"Generated Content Preview: {article.generated_content[:200]}...")
            else:
                print("❌ No generated content found!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_database_content()

