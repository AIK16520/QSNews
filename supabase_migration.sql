-- Supabase Migration SQL
-- Run this in your Supabase SQL Editor to create all tables

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL
);

-- Create industries table
CREATE TABLE IF NOT EXISTS industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL
);

-- Create articles table
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048) UNIQUE NOT NULL,
    title VARCHAR(512) NOT NULL,
    source VARCHAR(128) NOT NULL,
    published_date TIMESTAMP,
    summary TEXT,
    full_content TEXT,
    category_id INTEGER REFERENCES categories(id),
    fetched_date TIMESTAMP NOT NULL DEFAULT NOW(),
    your_analysis TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'not_included',
    user_content TEXT,
    ai_instructions TEXT,
    generated_content TEXT,
    final_content TEXT,
    commentary TEXT,
    newsletter_section VARCHAR(128),
    section_order INTEGER
);

-- Create newsletters table
CREATE TABLE IF NOT EXISTS newsletters (
    id SERIAL PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    source VARCHAR(128) NOT NULL,
    published_date TIMESTAMP,
    summary TEXT,
    full_content TEXT,
    plain_text TEXT,
    extracted_links JSONB,
    tags JSONB,
    industries JSONB,
    email_subject VARCHAR(512),
    from_email VARCHAR(256),
    received_date TIMESTAMP NOT NULL DEFAULT NOW(),
    archive_url VARCHAR(2048),
    fetched_date TIMESTAMP NOT NULL DEFAULT NOW(),
    your_analysis TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'not_included',
    user_content TEXT,
    ai_instructions TEXT,
    generated_content TEXT,
    final_content TEXT,
    commentary TEXT,
    newsletter_section VARCHAR(128),
    section_order INTEGER
);

-- Create article_industries junction table (many-to-many)
CREATE TABLE IF NOT EXISTS article_industries (
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    industry_id INTEGER REFERENCES industries(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, industry_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date);
CREATE INDEX IF NOT EXISTS idx_articles_category_id ON articles(category_id);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);

CREATE INDEX IF NOT EXISTS idx_newsletters_source ON newsletters(source);
CREATE INDEX IF NOT EXISTS idx_newsletters_published_date ON newsletters(published_date);
CREATE INDEX IF NOT EXISTS idx_newsletters_status ON newsletters(status);

CREATE INDEX IF NOT EXISTS idx_article_industries_article ON article_industries(article_id);
CREATE INDEX IF NOT EXISTS idx_article_industries_industry ON article_industries(industry_id);

-- Insert default categories
INSERT INTO categories (name) VALUES
    ('Tools and Products'),
    ('Legal and Regulations'),
    ('Funding and M&A'),
    ('Security and Privacy'),
    ('Events and Conferences'),
    ('Research and Studies')
ON CONFLICT (name) DO NOTHING;

-- Insert default industries
INSERT INTO industries (name) VALUES
    ('Healthcare and Medicine'),
    ('Manufacturing and Robotics'),
    ('Software and Development'),
    ('Finance and Banking'),
    ('Education and EdTech'),
    ('Retail and E-commerce'),
    ('Transportation and Autonomous Vehicles'),
    ('Media and Entertainment'),
    ('Agriculture and Food'),
    ('Energy and Utilities'),
    ('Legal and Law'),
    ('Marketing and Advertising'),
    ('Cybersecurity'),
    ('Government and Public Sector'),
    ('Real Estate and Construction'),
    ('Human Resources and Recruitment'),
    ('Customer Service and Support'),
    ('Telecommunications'),
    ('General AI')
ON CONFLICT (name) DO NOTHING;

-- Enable Row Level Security (RLS) - Optional but recommended
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE industries ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE newsletters ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_industries ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users (adjust as needed)
-- For now, allow all authenticated users full access
CREATE POLICY "Enable all for authenticated users" ON categories
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all for authenticated users" ON industries
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all for authenticated users" ON articles
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all for authenticated users" ON newsletters
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all for authenticated users" ON article_industries
    FOR ALL USING (auth.role() = 'authenticated');

-- If you want to allow service role (for backend) to bypass RLS:
-- ALTER TABLE categories FORCE ROW LEVEL SECURITY;
-- (repeat for other tables)

