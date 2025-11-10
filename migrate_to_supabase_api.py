"""
Migrate data from SQLite to Supabase using the Supabase API.
This is easier than direct PostgreSQL connection!

Usage:
    python migrate_to_supabase_api.py
"""

import os
import sys
import time
from datetime import datetime
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.database import get_session, Article, Newsletter, Category, Industry
import config

def get_supabase_client() -> Client:
    """Get Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY not found in environment.\n"
            "Add to your .env file:\n"
            "SUPABASE_URL=https://xxxxx.supabase.co\n"
            "SUPABASE_KEY=your-api-key"
        )
    
    return create_client(url, key)

def migrate_categories(sqlite_session, supabase: Client):
    """Migrate categories."""
    print("\n📁 Migrating Categories...")
    categories = sqlite_session.query(Category).all()
    
    for cat in categories:
        # Check if exists
        existing = supabase.table('categories').select('*').eq('name', cat.name).execute()
        if existing.data:
            print(f"  ✓ Category '{cat.name}' already exists")
        else:
            supabase.table('categories').insert({'name': cat.name}).execute()
            print(f"  + Added category '{cat.name}'")
    
    print(f"✅ Migrated {len(categories)} categories")

def migrate_industries(sqlite_session, supabase: Client):
    """Migrate industries."""
    print("\n🏭 Migrating Industries...")
    industries = sqlite_session.query(Industry).all()
    
    for ind in industries:
        # Check if exists
        existing = supabase.table('industries').select('*').eq('name', ind.name).execute()
        if existing.data:
            print(f"  ✓ Industry '{ind.name}' already exists")
        else:
            supabase.table('industries').insert({'name': ind.name}).execute()
            print(f"  + Added industry '{ind.name}'")
    
    print(f"✅ Migrated {len(industries)} industries")

def migrate_articles(sqlite_session, supabase: Client):
    """Migrate articles."""
    print("\n📰 Migrating Articles...")
    articles = sqlite_session.query(Article).all()
    
    # Get category and industry mappings
    categories_map = {}
    for cat in supabase.table('categories').select('id, name').execute().data:
        categories_map[cat['name']] = cat['id']
    
    industries_map = {}
    for ind in supabase.table('industries').select('id, name').execute().data:
        industries_map[ind['name']] = ind['id']
    
    migrated = 0
    skipped = 0
    
    for i, article in enumerate(articles, 1):
        # Check if exists by URL
        existing = supabase.table('articles').select('id').eq('url', article.url).execute()
        if existing.data:
            skipped += 1
            continue
        
        # Prepare article data
        article_data = {
            'url': article.url,
            'title': article.title,
            'source': article.source,
            'published_date': article.published_date.isoformat() if article.published_date else None,
            'summary': article.summary,
            'full_content': article.full_content,
            'category_id': categories_map.get(article.category.name) if article.category else None,
            'fetched_date': article.fetched_date.isoformat() if article.fetched_date else datetime.utcnow().isoformat(),
            'your_analysis': article.your_analysis,
            'status': article.status,
            'user_content': article.user_content,
            'ai_instructions': article.ai_instructions,
            'generated_content': article.generated_content,
            'final_content': article.final_content,
            'commentary': article.commentary,
            'newsletter_section': article.newsletter_section,
            'section_order': article.section_order
        }
        
        # Insert article with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = supabase.table('articles').insert(article_data).execute()
                new_article_id = result.data[0]['id']
                
                # Insert article-industry relationships
                for industry in article.industries:
                    industry_id = industries_map.get(industry.name)
                    if industry_id:
                        supabase.table('article_industries').insert({
                            'article_id': new_article_id,
                            'industry_id': industry_id
                        }).execute()
                
                migrated += 1
                break  # Success, exit retry loop
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️  Retry {attempt + 1}/{max_retries} for article {i}...")
                    time.sleep(2)  # Wait before retry
                else:
                    print(f"  ✗ Failed to migrate article {i}: {article.title[:50]}")
                    raise
        
        # Rate limiting - pause every 10 articles
        if migrated % 10 == 0:
            print(f"  📊 Migrated {migrated}/{len(articles)} articles...")
            time.sleep(0.5)  # Small delay to avoid overwhelming the API
    
    print(f"✅ Migrated {migrated} articles (skipped {skipped} duplicates)")

def migrate_newsletters(sqlite_session, supabase: Client):
    """Migrate newsletters."""
    print("\n📧 Migrating Newsletters...")
    newsletters = sqlite_session.query(Newsletter).all()
    
    migrated = 0
    skipped = 0
    
    for i, newsletter in enumerate(newsletters, 1):
        # Check if exists
        existing = supabase.table('newsletters').select('id').eq('title', newsletter.title).eq('source', newsletter.source).execute()
        if existing.data:
            skipped += 1
            continue
        
        # Prepare newsletter data
        newsletter_data = {
            'title': newsletter.title,
            'source': newsletter.source,
            'published_date': newsletter.published_date.isoformat() if newsletter.published_date else None,
            'summary': newsletter.summary,
            'full_content': newsletter.full_content,
            'plain_text': newsletter.plain_text,
            'extracted_links': newsletter.extracted_links,
            'tags': newsletter.tags,
            'industries': newsletter.industries,
            'email_subject': newsletter.email_subject,
            'from_email': newsletter.from_email,
            'received_date': newsletter.received_date.isoformat() if newsletter.received_date else datetime.utcnow().isoformat(),
            'archive_url': newsletter.archive_url,
            'fetched_date': newsletter.fetched_date.isoformat() if newsletter.fetched_date else datetime.utcnow().isoformat(),
            'your_analysis': newsletter.your_analysis,
            'status': newsletter.status,
            'user_content': newsletter.user_content,
            'ai_instructions': newsletter.ai_instructions,
            'generated_content': newsletter.generated_content,
            'final_content': newsletter.final_content,
            'commentary': newsletter.commentary,
            'newsletter_section': newsletter.newsletter_section,
            'section_order': newsletter.section_order
        }
        
        # Insert newsletter with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                supabase.table('newsletters').insert(newsletter_data).execute()
                migrated += 1
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️  Retry {attempt + 1}/{max_retries} for newsletter {i}...")
                    time.sleep(2)
                else:
                    print(f"  ✗ Failed to migrate newsletter {i}: {newsletter.title[:50]}")
                    raise
        
        if migrated % 10 == 0:
            print(f"  📊 Migrated {migrated}/{len(newsletters)} newsletters...")
            time.sleep(0.5)  # Rate limiting
    
    print(f"✅ Migrated {migrated} newsletters (skipped {skipped} duplicates)")

def main():
    """Main migration function."""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION - Using Supabase API")
    print("="*80)
    
    # Check credentials
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        print("\n❌ ERROR: Supabase credentials not found")
        print("\nAdd to your .env file:")
        print("SUPABASE_URL=https://xxxxx.supabase.co")
        print("SUPABASE_KEY=your-anon-or-service-key")
        print("\nGet these from: Supabase Dashboard → Settings → API")
        sys.exit(1)
    
    try:
        # Connect to databases
        print("\n🔌 Connecting...")
        sqlite_session = get_session()
        print(f"  ✓ Connected to SQLite: {config.DATABASE_PATH}")
        
        supabase = get_supabase_client()
        print(f"  ✓ Connected to Supabase API")
        
        # Get counts
        sqlite_article_count = sqlite_session.query(Article).count()
        sqlite_newsletter_count = sqlite_session.query(Newsletter).count()
        
        print(f"\n📊 Source Database (SQLite):")
        print(f"  - Articles: {sqlite_article_count}")
        print(f"  - Newsletters: {sqlite_newsletter_count}")
        
        # Confirm
        print("\n⚠️  This will migrate all data from SQLite to Supabase.")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Migration cancelled")
            return
        
        # Start migration
        start_time = datetime.now()
        
        # 1. Migrate categories and industries
        migrate_categories(sqlite_session, supabase)
        migrate_industries(sqlite_session, supabase)
        
        # 2. Migrate articles
        migrate_articles(sqlite_session, supabase)
        
        # 3. Migrate newsletters
        migrate_newsletters(sqlite_session, supabase)
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*80)
        print(f"✅ MIGRATION COMPLETE in {elapsed:.1f}s")
        print("="*80)
        
        # Final counts
        supabase_article_count = len(supabase.table('articles').select('id').execute().data)
        supabase_newsletter_count = len(supabase.table('newsletters').select('id').execute().data)
        
        print(f"\n📊 Destination Database (Supabase):")
        print(f"  - Articles: {supabase_article_count}")
        print(f"  - Newsletters: {supabase_newsletter_count}")
        
        print("\n🎉 Migration successful!")
        print("\nNote: For your app to use Supabase, you still need the database URL")
        print("for SQLAlchemy connections, not just the API.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sqlite_session.close()

if __name__ == "__main__":
    main()

