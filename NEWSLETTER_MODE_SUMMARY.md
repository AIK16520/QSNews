# Newsletter Mode - Complete Implementation Summary

## Overview
Added a complete newsletter mode to QSNews that pulls newsletters from Gmail, scrapes historic archives, generates AI summaries with embedded links, and displays them in an optimized dashboard.

---

## ✅ What Was Built

### 1. Backend System

#### Database (src/utils/database.py)
- **New `Newsletter` table** with fields:
  - `title`, `source`, `published_date`
  - `summary` - AI-generated with embedded markdown links
  - `full_content` - Original HTML
  - `plain_text` - Text version
  - `extracted_links` - JSON array: `[{title, url, context}]`
  - Same workflow fields as articles (status, your_analysis, etc.)

#### Newsletter Fetcher (src/fetchers/newsletter_fetcher.py)
- **IMAP Gmail integration** - Fetches from Gmail inbox
- Auto-identifies newsletter source from email
- Extracts HTML/plain text and all links
- Connects via app password (2FA required)

#### Archive Scraper (src/fetchers/newsletter_archive_scraper.py)
- **Scrapes public RSS archives** for historic content
- Currently supports:
  - ✅ Ben's Bites (Beehiiv RSS)
  - ✅ Last Week in AI (WordPress RSS)
  - ✅ TheSequence (Substack RSS)
  - ✅ One Useful Thing (WordPress RSS)
- Extracts 30 days of historic newsletters

#### Newsletter Processor (src/processors/newsletter_processor.py)
- **AI-powered summary generation** using OpenAI
- Creates 2-3 sentence summaries
- **Embeds links inline** in markdown format
- Example: "Discusses [OpenAI's deal](link), [Google's updates](link)..."

#### Processing Pipeline (src/processors/newsletter_pipeline.py)
- Orchestrates fetching → processing → storage
- Deduplication by title + source + date
- Handles both Gmail and archive sources

### 2. CLI Commands (src/main.py)

```bash
# Fetch from Gmail inbox (past 7 days)
python src/main.py fetch-newsletters

# Scrape historic archives (past 30 days)
python src/main.py scrape-newsletter-archives

# Run both (Gmail + archives)
python src/main.py newsletter-full-run

# Check database stats
python src/main.py init-db
```

### 3. Dashboard UI (dashboard/app.py)

#### New Features:
- **Content Type Selector** - Switch between Articles / Newsletters
- **Newsletter Review Page** with optimized layout

#### Optimized Display (Minimal Clicks):
```
┌─────────────────────────────────────────────────────────────┐
│ [Title Link] · Source · Date                              ✓ │
│ Summary with embedded [links](url) directly visible...      │
│                                                              │
│ └─ 📝 View Links & Add Notes (expandable)                   │
│    ├─ 1. [Link Title](url)                                  │
│    │   Context about this link...                           │
│    ├─ 2. [Link Title](url)                                  │
│    │   Context about this link...                           │
│    └─ Your Analysis: [text area]                            │
│       [💾 Save Notes]                                        │
├─────────────────────────────────────────────────────────────┤
```

#### Features:
- **No clicking needed** - Title, summary, and links visible immediately
- **Right-aligned checkmark** - ✓ (green) if included, ✗ (red) if not
- **One-click toggle** - Click checkmark to include/exclude
- **Expand for details** - Links list + editor notes only when needed
- **Filter by** - Source, Status, Date Range
- **Statistics** - Total, Included, Not Included counts

### 4. GitHub Actions Workflow (.github/workflows/newsletter_collection.yml)

**Automated Daily Collection:**
- Runs daily at 9 AM UTC
- Fetches new newsletters from Gmail
- Scrapes archives weekly (Mondays only)
- Auto-commits updated database

**Required Secrets:**
- `OPENAI_API_KEY` - Your OpenAI key
- `NEWSLETTER_GMAIL` - qsnewssub@gmail.com
- `GMAIL_APP_PASS` - 16-character app password

---

## 📊 Current Data

**Database:** `data/articles.db`
- **42 newsletters** already collected
- **Sources:**
  - Ben's Bites: 20 newsletters
  - TheSequence: 17 newsletters
  - Last Week in AI: 4 newsletters
  - One Useful Thing: 1 newsletter

---

## 🚀 How to Use

### 1. View Newsletters in Dashboard

```bash
streamlit run dashboard/app.py
```

Then:
1. Select **"Newsletters"** from Content Type radio button
2. View summaries with embedded links (no clicking!)
3. Click ✓/✗ to include/exclude
4. Expand "📝 View Links & Add Notes" for details

### 2. Collect Newsletters Manually

```bash
# Fetch from Gmail (requires app password set up)
python src/main.py fetch-newsletters

# Scrape historic newsletters from archives
python src/main.py scrape-newsletter-archives

# Run both
python src/main.py newsletter-full-run
```

### 3. Set Up Automated Collection

1. Push to GitHub
2. Go to repo Settings → Secrets and variables → Actions
3. Add secrets:
   - `OPENAI_API_KEY`
   - `NEWSLETTER_GMAIL`
   - `GMAIL_APP_PASS`
4. Workflow runs automatically daily at 9 AM UTC

---

## 🔧 Gmail Setup (One-Time)

### Enable IMAP:
1. Go to Gmail Settings → Forwarding and POP/IMAP
2. Enable IMAP
3. Save Changes

### Create App Password:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (required)
3. Go to https://myaccount.google.com/apppasswords
4. Select App: "Mail"
5. Select Device: "Other (Custom name)" → "Newsletter Fetcher"
6. Click Generate
7. Copy 16-character password
8. Add to `.env`:
   ```
   GMAIL_APP_PASS=abcdefghijklmnop
   ```

---

## 📝 Newsletter Summary Format

Summaries are AI-generated with embedded links:

**Example:**
> This week's Ben's Bites discusses [OpenAI's $38B compute deal with Amazon](https://openai.com/aws-partnership), highlights [Anthropic's Claude integration with Excel](https://anthropic.com/excel), and covers [Google's new enterprise AI offerings](https://google.com/ai-enterprise).

Links are embedded **inline** in the summary text, not as a separate list.

---

## 🎯 Newsletter Sources

### Currently Subscribed (via Gmail):
- The Rundown
- Superhuman AI
- Ben's Bites
- Mindstream
- AI Breakfast
- Future Tools
- TLDR AI
- The AI Exchange

### Archive Scrapers (RSS):
- ✅ Ben's Bites (Beehiiv RSS)
- ✅ Last Week in AI (WordPress RSS)
- ✅ TheSequence (Substack RSS)
- ✅ One Useful Thing (WordPress RSS)

### To Add More Newsletters:
Edit `src/fetchers/newsletter_archive_scraper.py` → `NEWSLETTER_ARCHIVES` dictionary

---

## 🔄 Workflow

```
New Newsletter Arrives in Gmail
       ↓
Daily GitHub Action Runs
       ↓
IMAP Fetches Email → Extract HTML + Links
       ↓
AI Generates Summary with Embedded Links
       ↓
Save to Database (newsletters table)
       ↓
View in Dashboard → Include/Exclude
       ↓
Export in Final Report
```

---

## 📁 File Structure

```
QSNews/
├── src/
│   ├── fetchers/
│   │   ├── newsletter_fetcher.py          # IMAP Gmail fetcher
│   │   └── newsletter_archive_scraper.py  # RSS archive scraper
│   ├── processors/
│   │   ├── newsletter_processor.py        # AI summary generator
│   │   └── newsletter_pipeline.py         # Processing pipeline
│   └── utils/
│       └── database.py                    # Newsletter model
├── dashboard/
│   └── app.py                             # Streamlit UI (updated)
├── .github/
│   └── workflows/
│       └── newsletter_collection.yml      # Daily automation
├── data/
│   └── articles.db                        # SQLite database
└── .env                                   # Credentials
```

---

## ✨ Key Features

1. **Minimal Clicks** - Everything visible without expanding
2. **Embedded Links** - Links in summary text, not separate list
3. **One-Click Toggle** - ✓/✗ button to include/exclude
4. **Smart Summaries** - AI-generated with context
5. **Historic Data** - Scrapes 30 days of archives
6. **Auto Collection** - Daily GitHub Actions workflow
7. **Same Workflow** - Uses same status system as articles

---

## 🎨 Dashboard UI Design

### Main View (No Clicks Required):
- **Title** (clickable link to original)
- **Source** + **Date**
- **Summary** with embedded markdown links
- **✓/✗ Button** (right-aligned, one-click toggle)

### Expandable Section (Optional):
- **Link List** - All links with context
- **Your Analysis** - Editor notes text area
- **Save Notes** - Button to save

---

## 🚧 Future Enhancements

1. **More Archive Scrapers** - Add The Rundown, TLDR AI, Superhuman AI
2. **Link Explanations** - Use AI to explain what each link is about
3. **Newsletter Generation** - Generate output using included newsletters
4. **Search** - Full-text search across newsletter summaries
5. **Tags** - Tag newsletters by topic (AI, Research, Product, etc.)

---

## 🐛 Troubleshooting

### "Invalid credentials" error:
- Make sure you're using **App Password**, not regular Gmail password
- Enable 2-Factor Authentication first
- Generate new app password at https://myaccount.google.com/apppasswords

### No newsletters showing:
- Check if emails are in Gmail inbox
- Run `python src/main.py fetch-newsletters` manually
- Check logs for errors

### Dashboard not showing newsletters:
- Make sure database has newsletters: `python src/main.py init-db`
- Select "Newsletters" from Content Type radio button
- Check filters (try "Clear Filters")

---

## 📞 Support

- **CLI Help**: `python src/main.py --help`
- **Database Stats**: `python src/main.py init-db`
- **Check Newsletters**: `python check_newsletters.py`

---

**Status:** ✅ Fully Implemented & Tested
**Last Updated:** 2025-11-04
