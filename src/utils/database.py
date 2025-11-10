"""
Database models and utilities for the AI Newsletter Tool.
Defines Article, Category, and Industry models with SQLAlchemy ORM.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Table,
    Index,
    JSON
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
    Session
)

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Association table for Article-Industry many-to-many relationship
article_industries = Table(
    'article_industries',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True),
    Column('industry_id', Integer, ForeignKey('industries.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_article_industries_article', 'article_id'),
    Index('idx_article_industries_industry', 'industry_id')
)


class Category(Base):
    """Category model - represents article categories (single choice)."""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)

    # Relationships
    articles = relationship('Article', back_populates='category')

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary (for Supabase API)."""
        instance = cls()
        instance.id = data.get('id')
        instance.name = data.get('name')
        return instance


class Industry(Base):
    """Industry model - represents industry tags (multiple choice)."""
    __tablename__ = 'industries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)

    # Relationships
    articles = relationship('Article', secondary=article_industries, back_populates='industries')

    def __repr__(self):
        return f"<Industry(id={self.id}, name='{self.name}')>"


class Article(Base):
    """Article model - represents news articles with full content and metadata."""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    source = Column(String(128), nullable=False, index=True)
    published_date = Column(DateTime, nullable=True, index=True)
    summary = Column(Text, nullable=True)  # LLM-generated summary
    full_content = Column(Text, nullable=True)  # Scraped content

    # Foreign key to category (1:N relationship)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)

    # Metadata
    fetched_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    your_analysis = Column(Text, nullable=True)  # User input from dashboard
    status = Column(String(32), default='not_included', nullable=False, index=True)  # included, not_included, in_review, generated, finalized

    # Review workflow fields
    user_content = Column(Text, nullable=True)  # Additional user content/context for review
    ai_instructions = Column(Text, nullable=True)  # Instructions for AI generation
    generated_content = Column(Text, nullable=True)  # AI-generated article
    final_content = Column(Text, nullable=True)  # Final version after user tweaks

    # Newsletter Builder fields (manual control)
    commentary = Column(Text, nullable=True)  # User's manual insights for this item
    newsletter_section = Column(String(128), nullable=True)  # e.g., "Top Story", "Quick Links"
    section_order = Column(Integer, nullable=True)  # Order within the section

    # Relationships
    category = relationship('Category', back_populates='articles')
    industries = relationship('Industry', secondary=article_industries, back_populates='articles')

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source='{self.source}', status='{self.status}')>"

    def to_dict(self):
        """Convert article to dictionary for easy serialization."""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'summary': self.summary,
            'full_content': self.full_content,
            'category': self.category.name if self.category else None,
            'industries': [ind.name for ind in self.industries],
            'fetched_date': self.fetched_date.isoformat() if self.fetched_date else None,
            'your_analysis': self.your_analysis,
            'status': self.status,
            'user_content': self.user_content,
            'ai_instructions': self.ai_instructions,
            'generated_content': self.generated_content,
            'final_content': self.final_content
        }


class Newsletter(Base):
    """Newsletter model - represents email newsletters with embedded links."""
    __tablename__ = 'newsletters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)  # Newsletter subject/title
    source = Column(String(128), nullable=False, index=True)  # e.g., "The Rundown", "Ben's Bites"
    published_date = Column(DateTime, nullable=True, index=True)
    summary = Column(Text, nullable=True)  # Brief AI-generated summary with embedded links
    full_content = Column(Text, nullable=True)  # Original email HTML content
    plain_text = Column(Text, nullable=True)  # Plain text version

    # Extracted links stored as JSON: [{"title": "...", "url": "...", "context": "..."}]
    extracted_links = Column(JSON, nullable=True)

    # AI-extracted topic tags stored as JSON: ["AI", "Cloud", "Research"]
    tags = Column(JSON, nullable=True)
    
    # AI-extracted industries stored as JSON: ["Healthcare", "Finance", "Enterprise"]
    industries = Column(JSON, nullable=True)

    # Email metadata
    email_subject = Column(String(512), nullable=True)
    from_email = Column(String(256), nullable=True)
    received_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Archive URL (optional - only for newsletters from public archives)
    archive_url = Column(String(2048), nullable=True)

    # Same workflow as articles
    fetched_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    your_analysis = Column(Text, nullable=True)  # Editor's notes
    status = Column(String(32), default='not_included', nullable=False, index=True)

    # Review workflow fields
    user_content = Column(Text, nullable=True)
    ai_instructions = Column(Text, nullable=True)
    generated_content = Column(Text, nullable=True)
    final_content = Column(Text, nullable=True)

    # Newsletter Builder fields (manual control)
    commentary = Column(Text, nullable=True)  # User's manual insights for this item
    newsletter_section = Column(String(128), nullable=True)  # e.g., "Top Story", "Quick Links"
    section_order = Column(Integer, nullable=True)  # Order within the section

    def __repr__(self):
        return f"<Newsletter(id={self.id}, title='{self.title[:50]}...', source='{self.source}', status='{self.status}')>"

    def to_dict(self):
        """Convert newsletter to dictionary for easy serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'summary': self.summary,
            'full_content': self.full_content,
            'plain_text': self.plain_text,
            'extracted_links': self.extracted_links,
            'tags': self.tags,
            'industries': self.industries,
            'email_subject': self.email_subject,
            'from_email': self.from_email,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'archive_url': self.archive_url,
            'fetched_date': self.fetched_date.isoformat() if self.fetched_date else None,
            'your_analysis': self.your_analysis,
            'status': self.status,
            'user_content': self.user_content,
            'ai_instructions': self.ai_instructions,
            'generated_content': self.generated_content,
            'final_content': self.final_content
        }


# Database engine and session management
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine (supports both SQLite and PostgreSQL/Supabase)."""
    global _engine
    if _engine is None:
        if config.USE_SUPABASE and config.SUPABASE_DB_URL:
            # Use Supabase (PostgreSQL)
            _engine = create_engine(
                config.SUPABASE_DB_URL,
                echo=False,  # Set to True for SQL debugging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600  # Recycle connections after 1 hour
            )
            logger.info(f"Database engine created: Supabase PostgreSQL")
        else:
            # Use local SQLite
            # Ensure data directory exists
            db_dir = os.path.dirname(config.DATABASE_PATH)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")

            # Create engine
            _engine = create_engine(
                f'sqlite:///{config.DATABASE_PATH}',
                echo=False,  # Set to True for SQL debugging
                connect_args={'check_same_thread': False}  # Needed for SQLite
            )
            logger.info(f"Database engine created: {config.DATABASE_PATH}")

    return _engine


def get_session():
    """Get a new database session. Creates tables if they don't exist."""
    # Check if we should use Supabase API
    if config.USE_SUPABASE and config.SUPABASE_URL and config.SUPABASE_KEY:
        from src.utils.database_supabase import get_supabase_session
        logger.info("Using Supabase API")
        return get_supabase_session()
    
    # Use SQLAlchemy for SQLite
    global _SessionLocal

    engine = get_engine()

    # Create all tables if they don't exist
    Base.metadata.create_all(engine)

    # Create session factory if not exists
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    return _SessionLocal()


def seed_database(session: Optional[Session] = None):
    """
    Seed the database with categories and industries from config.
    Idempotent - safe to run multiple times.
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True

    try:
        # Seed categories
        categories_added = 0
        for category_name in config.CATEGORIES:
            existing = session.query(Category).filter_by(name=category_name).first()
            if not existing:
                category = Category(name=category_name)
                session.add(category)
                categories_added += 1

        # Seed industries
        industries_added = 0
        for industry_name in config.INDUSTRIES:
            existing = session.query(Industry).filter_by(name=industry_name).first()
            if not existing:
                industry = Industry(name=industry_name)
                session.add(industry)
                industries_added += 1

        session.commit()

        if categories_added > 0 or industries_added > 0:
            logger.info(f"Database seeded: {categories_added} categories, {industries_added} industries added")
        else:
            logger.info("Database already seeded")

    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        if close_session:
            session.close()


def get_or_create_category(session: Session, name: str) -> Optional[Category]:
    """Get existing category by name or return None."""
    return session.query(Category).filter_by(name=name).first()


def get_or_create_industry(session: Session, name: str) -> Optional[Industry]:
    """Get existing industry by name or return None."""
    return session.query(Industry).filter_by(name=name).first()


def init_database():
    """Initialize database: create tables and seed data."""
    logger.info("Initializing database...")
    session = get_session()
    try:
        seed_database(session)
        logger.info("Database initialized successfully")
    finally:
        session.close()


if __name__ == "__main__":
    # For testing: initialize database when run directly
    init_database()

    # Print stats
    session = get_session()
    try:
        category_count = session.query(Category).count()
        industry_count = session.query(Industry).count()
        article_count = session.query(Article).count()

        print(f"\nDatabase Statistics:")
        print(f"  Categories: {category_count}")
        print(f"  Industries: {industry_count}")
        print(f"  Articles: {article_count}")

        print(f"\nCategories:")
        for cat in session.query(Category).all():
            print(f"  - {cat.name}")

        print(f"\nIndustries:")
        for ind in session.query(Industry).all():
            print(f"  - {ind.name}")

    finally:
        session.close()
