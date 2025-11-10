# Quick Start: Update Newsletter Links

## 🚀 Quick Commands

### 1. Preview Changes (Safe - No Database Modifications)
```bash
cd QSNews
python scripts/update_newsletter_links.py --dry-run
```

### 2. See Before/After Example
```bash
python scripts/update_newsletter_links.py --sample
```

### 3. Update All Newsletters
```bash
python scripts/update_newsletter_links.py
```

---

## 📋 Step-by-Step Guide

### Step 1: Backup Your Database (Recommended)

**Windows PowerShell:**
```powershell
Copy-Item "QSNews\data\ai_newsletter.db" -Destination "QSNews\data\ai_newsletter.db.backup"
```

**Windows CMD:**
```cmd
copy QSNews\data\ai_newsletter.db QSNews\data\ai_newsletter.db.backup
```

**Mac/Linux:**
```bash
cp QSNews/data/ai_newsletter.db QSNews/data/ai_newsletter.db.backup
```

### Step 2: Preview What Will Change

```bash
cd QSNews
python scripts/update_newsletter_links.py --dry-run
```

**Expected Output:**
```
======================================================================
UPDATING NEWSLETTER LINKS
Total newsletters: 25
Dry run: True
======================================================================

⚠️  DRY RUN MODE - No changes will be saved

[1/25] Processing newsletter ID 1
Processing: Ben's Bites - OpenAI, Amazon, and $38B
  Links: 42 -> 15 (filtered 27)

[2/25] Processing newsletter ID 2
...

======================================================================
UPDATE SUMMARY
======================================================================
Total newsletters: 25
Successfully updated: 23
Skipped (no content): 2
Failed: 0

⚠️  DRY RUN - No changes were saved to database
Run without --dry-run to actually update the database
======================================================================
```

### Step 3: See Detailed Before/After for One Newsletter

```bash
python scripts/update_newsletter_links.py --sample
```

**Example Output:**
```
======================================================================
BEFORE/AFTER COMPARISON
======================================================================
Newsletter: Ben's Bites - OpenAI, Amazon, and $38B

CURRENT LINKS (in database):
----------------------------------------------------------------------
1. Read Online
   URL: https://bensbites.beehiiv.com/p/...
   Context: (none)

2. Sign Up
   URL: https://bensbites.com/subscribe
   Context: (none)

3. OpenAI's $38B compute deal with Amazon
   URL: https://techcrunch.com/...
   Context: OpenAI has secured a massive...

... (showing first 10 of 42)
Total current links: 42

======================================================================
NEW LINKS (after update):
----------------------------------------------------------------------
1. OpenAI's $38B compute deal with Amazon
   URL: https://techcrunch.com/...
   Explanation: OpenAI has secured a massive $38B compute deal with Amazon.
   Domain: techcrunch.com

2. Coca-Cola doubles down on AI holiday ads
   URL: https://marketing.com/...
   Explanation: Coca-Cola launches new AI-generated holiday advertising campaign.
   Domain: marketing.com

... (showing first 10 of 15)
Total new links: 15

======================================================================
STATISTICS:
Before: 42 links
After: 15 links
Filtered: 27 links
Reduction: 64.3%
======================================================================
```

### Step 4: Apply Updates

Once you're satisfied with the preview:

```bash
python scripts/update_newsletter_links.py
```

**Progress Output:**
```
======================================================================
UPDATING NEWSLETTER LINKS
Total newsletters: 25
Dry run: False
======================================================================

[1/25] Processing newsletter ID 1
Processing: Ben's Bites - OpenAI, Amazon, and $38B
  Links: 42 -> 15 (filtered 27)
  ✓ Committed batch (total updated: 10)

[11/25] Processing newsletter ID 11
...

✓ Final commit complete

======================================================================
UPDATE SUMMARY
======================================================================
Total newsletters: 25
Successfully updated: 23
Skipped (no content): 2
Failed: 0

✓ All changes saved to database
======================================================================
```

### Step 5: Verify in Dashboard

```bash
streamlit run dashboard/app.py
```

1. Switch to "Newsletters" content type
2. Navigate to "Newsletter Review & Generate"
3. Include some newsletters
4. Click "Produce ALL"
5. Verify the output is cleaner with better explanations

---

## 🎯 Advanced Usage

### Update Only Specific Newsletters

If you only want to update certain newsletters:

```bash
# Update newsletters with IDs 1, 5, and 10
python scripts/update_newsletter_links.py --ids 1,5,10
```

### See Before/After for Specific Newsletter

```bash
# Show comparison for newsletter ID 5
python scripts/update_newsletter_links.py --sample-id 5
```

### Custom Batch Size

If you have many newsletters, adjust batch commit size:

```bash
# Commit every 20 newsletters instead of default 10
python scripts/update_newsletter_links.py --batch-size 20
```

---

## ⚠️ Common Issues

### Issue 1: "Database is locked"

**Cause:** Dashboard is still running

**Solution:**
1. Close the Streamlit dashboard (Ctrl+C in terminal)
2. Run the update script
3. Restart dashboard when done

### Issue 2: "No newsletters found"

**Cause:** No newsletters in database yet

**Solution:**
1. Fetch newsletters first:
   ```bash
   python src/main.py fetch-newsletters
   # or
   python src/main.py scrape-newsletter-archives
   ```
2. Then run the update script

### Issue 3: Script runs but no changes

**Cause:** Probably in dry-run mode

**Solution:** Remove `--dry-run` flag:
```bash
python scripts/update_newsletter_links.py  # Without --dry-run
```

---

## 📊 What Gets Filtered

### ❌ Removed Links

- Navigation: "Sign Up", "Subscribe", "Unsubscribe"
- Utility: "Read Online", "Advertise", "About Us"
- Tracking URLs: Mailchimp, tracking pixels, etc.
- Social profiles: Twitter/LinkedIn profile links (not article links)
- App stores: App Store, Google Play links

### ✅ Kept Links

- Article links
- Research papers
- Product announcements
- News articles
- Blog posts
- Technical documentation
- Case studies

---

## 🔄 Rollback (If Needed)

If you need to restore the old data:

**Windows PowerShell:**
```powershell
Copy-Item "QSNews\data\ai_newsletter.db.backup" -Destination "QSNews\data\ai_newsletter.db" -Force
```

**Windows CMD:**
```cmd
copy /Y QSNews\data\ai_newsletter.db.backup QSNews\data\ai_newsletter.db
```

**Mac/Linux:**
```bash
cp QSNews/data/ai_newsletter.db.backup QSNews/data/ai_newsletter.db
```

---

## ✅ Verification Checklist

After running the update:

- [ ] Database backup created
- [ ] Dry-run completed successfully
- [ ] Sample output looks good
- [ ] Update script completed without errors
- [ ] Dashboard displays cleaner links
- [ ] "Produce ALL" output is improved
- [ ] No important links were filtered

---

## 💡 Tips

1. **Always run dry-run first** to see what will change
2. **Check sample output** before bulk update
3. **Backup your database** before making changes
4. **Close the dashboard** before running update script
5. **Verify in dashboard** after update

---

## 🆘 Need Help?

If something goes wrong:

1. **Restore from backup** (see Rollback section above)
2. **Check the logs** in the terminal output
3. **Run with dry-run** to diagnose issues
4. **Check specific newsletter** with `--sample-id`

---

## Summary

```bash
# Full workflow in 4 commands:
cd QSNews
python scripts/update_newsletter_links.py --dry-run    # Preview
python scripts/update_newsletter_links.py --sample     # See example
python scripts/update_newsletter_links.py              # Apply
streamlit run dashboard/app.py                         # Verify
```

**Expected Results:**
- ✅ 50-70% fewer links per newsletter
- ✅ All remaining links are actual content
- ✅ Better explanations for each link
- ✅ Cleaner dashboard output

---

**Last Updated:** November 4, 2024




