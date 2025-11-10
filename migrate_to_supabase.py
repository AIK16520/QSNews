"""
Migrate data from SQLite to Supabase (PostgreSQL).

This script copies all data from your local SQLite database to Supabase.
Run this AFTER executing the supabase_migration.sql in your Supabase SQL Editor.

Usage:
    python migrate_to_supabase.py
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.database import Article, Newsletter, Category, Industry, Base, article_industries
import config

def get_sqlite_session():
    """Get SQLite session."""
    sqlite_engine = create_engine(f'sqlite:///{config.DATABASE_PATH}')
    Session = sessionmaker(bind=sqlite_engine)
    return Session()

def get_supabase_session():
    """Get Supabase (PostgreSQL) session."""
    if not config.SUPABASE_DB_URL:
        raise ValueError("SUPABASE_DB_URL not set in environment")
    
    postgres_engine = create_engine(config.SUPABASE_DB_URL)
    Session = sessionmaker(bind=postgres_engine)
    return Session()

def migrate_categories(sqlite_session, supabase_session):
    """Migrate categories."""
    print("\n📁 Migrating Categories...")
    categories = sqlite_session.query(Category).all()
    
    # Create mapping of old ID to new ID
    id_mapping = {}
    
    for cat in categories:
        # Check if exists
        existing = supabase_session.query(Category).filter_by(name=cat.name).first()
        if existing:
            id_mapping[cat.id] = existing.id
            print(f"  ✓ Category '{cat.name}' already exists (id: {existing.id})")
        else:
            new_cat = Category(name=cat.name)
            supabase_session.add(new_cat)
            supabase_session.flush()  # Get the new ID
            id_mapping[cat.id] = new_cat.id
            print(f"  + Added category '{cat.name}' (new id: {new_cat.id})")
    
    supabase_session.commit()
    print(f"✅ Migrated {len(categories)} categories")
    return id_mapping

def migrate_industries(sqlite_session, supabase_session):
    """Migrate industries."""
    print("\n🏭 Migrating Industries...")
    industries = sqlite_session.query(Industry).all()
    
    # Create mapping of old ID to new ID
    id_mapping = {}
    
    for ind in industries:
        # Check if exists
        existing = supabase_session.query(Industry).filter_by(name=ind.name).first()
        if existing:
            id_mapping[ind.id] = existing.id
            print(f"  ✓ Industry '{ind.name}' already exists (id: {existing.id})")
        else:
            new_ind = Industry(name=ind.name)
            supabase_session.add(new_ind)
            supabase_session.flush()
            id_mapping[ind.id] = new_ind.id
            print(f"  + Added industry '{ind.name}' (new id: {new_ind.id})")
    
    supabase_session.commit()
    print(f"✅ Migrated {len(industries)} industries")
    return id_mapping

def migrate_articles(sqlite_session, supabase_session, category_mapping, industry_mapping):
    """Migrate articles."""
    print("\n📰 Migrating Articles...")
    articles = sqlite_session.query(Article).all()
    
    migrated = 0
    skipped = 0
    
    for article in articles:
        # Check if exists by URL
        existing = supabase_session.query(Article).filter_by(url=article.url).first()
        if existing:
            skipped += 1
            continue
        
        # Create new article
        new_article = Article(
            url=article.url,
            title=article.title,
            source=article.source,
            published_date=article.published_date,
            summary=article.summary,
            full_content=article.full_content,
            category_id=category_mapping.get(article.category_id) if article.category_id else None,
            fetched_date=article.fetched_date,
            your_analysis=article.your_analysis,
            status=article.status,
            user_content=article.user_content,
            ai_instructions=article.ai_instructions,
            generated_content=article.generated_content,
            final_content=article.final_content,
            commentary=article.commentary,
            newsletter_section=article.newsletter_section,
            section_order=article.section_order
        )
        
        supabase_session.add(new_article)
        supabase_session.flush()  # Get the new ID
        
        # Migrate article-industry relationships
        for industry in article.industries:
            new_industry_id = industry_mapping.get(industry.id)
            if new_industry_id:
                # Insert into junction table
                stmt = article_industries.insert().values(
                    article_id=new_article.id,
                    industry_id=new_industry_id
                )
                supabase_session.execute(stmt)
        
        migrated += 1
        if migrated % 10 == 0:
            print(f"  📊 Migrated {migrated}/{len(articles)} articles...")
            supabase_session.commit()  # Commit in batches
    
    supabase_session.commit()
    print(f"✅ Migrated {migrated} articles (skipped {skipped} duplicates)")

def migrate_newsletters(sqlite_session, supabase_session):
    """Migrate newsletters."""
    print("\n📧 Migrating Newsletters...")
    newsletters = sqlite_session.query(Newsletter).all()
    
    migrated = 0
    skipped = 0
    
    for newsletter in newsletters:
        # Check if exists by title + source + published_date
        existing = supabase_session.query(Newsletter).filter_by(
            title=newsletter.title,
            source=newsletter.source,
            published_date=newsletter.published_date
        ).first()
        
        if existing:
            skipped += 1
            continue
        
        # Create new newsletter
        new_newsletter = Newsletter(
            title=newsletter.title,
            source=newsletter.source,
            published_date=newsletter.published_date,
            summary=newsletter.summary,
            full_content=newsletter.full_content,
            plain_text=newsletter.plain_text,
            extracted_links=newsletter.extracted_links,
            tags=newsletter.tags,
            industries=newsletter.industries,
            email_subject=newsletter.email_subject,
            from_email=newsletter.from_email,
            received_date=newsletter.received_date,
            archive_url=newsletter.archive_url,
            fetched_date=newsletter.fetched_date,
            your_analysis=newsletter.your_analysis,
            status=newsletter.status,
            user_content=newsletter.user_content,
            ai_instructions=newsletter.ai_instructions,
            generated_content=newsletter.generated_content,
            final_content=newsletter.final_content,
            commentary=newsletter.commentary,
            newsletter_section=newsletter.newsletter_section,
            section_order=newsletter.section_order
        )
        
        supabase_session.add(new_newsletter)
        migrated += 1
        
        if migrated % 10 == 0:
            print(f"  📊 Migrated {migrated}/{len(newsletters)} newsletters...")
            supabase_session.commit()  # Commit in batches
    
    supabase_session.commit()
    print(f"✅ Migrated {migrated} newsletters (skipped {skipped} duplicates)")

def main():
    """Main migration function."""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION - SQLite to PostgreSQL")
    print("="*80)
    
    # Check Supabase URL
    if not config.SUPABASE_DB_URL:
        print("\n❌ ERROR: SUPABASE_DB_URL not found in environment")
        print("\nAdd to your .env file:")
        print("SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT].supabase.co:5432/postgres")
        sys.exit(1)
    
    try:
        # Connect to both databases
        print("\n🔌 Connecting to databases...")
        sqlite_session = get_sqlite_session()
        print(f"  ✓ Connected to SQLite: {config.DATABASE_PATH}")
        
        supabase_session = get_supabase_session()
        print(f"  ✓ Connected to Supabase")
        
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
        
        # 1. Migrate categories and industries (needed first for foreign keys)
        category_mapping = migrate_categories(sqlite_session, supabase_session)
        industry_mapping = migrate_industries(sqlite_session, supabase_session)
        
        # 2. Migrate articles
        migrate_articles(sqlite_session, supabase_session, category_mapping, industry_mapping)
        
        # 3. Migrate newsletters
        migrate_newsletters(sqlite_session, supabase_session)
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*80)
        print(f"✅ MIGRATION COMPLETE in {elapsed:.1f}s")
        print("="*80)
        
        # Final counts
        supabase_article_count = supabase_session.query(Article).count()
        supabase_newsletter_count = supabase_session.query(Newsletter).count()
        
        print(f"\n📊 Destination Database (Supabase):")
        print(f"  - Articles: {supabase_article_count}")
        print(f"  - Newsletters: {supabase_newsletter_count}")
        
        print("\n🎉 Next Steps:")
        print("  1. Update your .env to set USE_SUPABASE=true")
        print("  2. Test your application with Supabase")
        print("  3. Update GitHub Actions secrets with SUPABASE_DB_URL")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sqlite_session.close()
        supabase_session.close()

if __name__ == "__main__":
    main()

