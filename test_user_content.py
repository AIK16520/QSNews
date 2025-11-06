#!/usr/bin/env python3
"""
Test script to verify user content emphasis in AI generation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.utils.database import get_session, Article
from src.processors.article_generator import build_context_from_articles

def test_user_content_emphasis():
    """Test that user content is properly emphasized in context building."""
    print("🔍 Testing User Content Emphasis")
    print("=" * 50)
    
    session = get_session()
    
    try:
        # Get articles with status 'generated'
        articles = session.query(Article).filter_by(status='generated').all()
        
        if not articles:
            print("❌ No articles with status 'generated' found")
            return
        
        article = articles[0]
        print(f"📄 Testing with article: {article.title}")
        print(f"📝 User content: {article.user_content}")
        print(f"🤖 AI instructions: {article.ai_instructions}")
        print(f"📊 Your analysis: {article.your_analysis}")
        
        # Test context building
        print("\n🚀 Testing context building...")
        context = build_context_from_articles(articles, article.user_content)
        
        print(f"\n📊 Context length: {len(context)} characters")
        print(f"\n📄 Generated context:")
        print("-" * 50)
        print(context)
        print("-" * 50)
        
        # Check if user content appears first
        if "EDITOR'S ADDITIONAL CONTENT (HIGHEST PRIORITY)" in context:
            print("✅ User additional content is prioritized!")
        else:
            print("❌ User additional content not found in priority section")
        
        # Check if user analysis appears prominently
        if "EDITOR'S ANALYSIS FOR EACH ARTICLE (VERY IMPORTANT)" in context:
            print("✅ User analysis is prominently featured!")
        else:
            print("❌ User analysis not found in important section")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_user_content_emphasis()

