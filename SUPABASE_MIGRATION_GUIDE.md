# 🚀 Supabase Migration Guide

This guide will help you migrate your QSNews database from SQLite to Supabase (PostgreSQL).

## 📋 Prerequisites

- [x] Supabase organization created
- [ ] Supabase project created
- [ ] Database password saved

## 🎯 Step-by-Step Migration

### Step 1: Create a Supabase Project

1. Go to https://supabase.com/dashboard
2. Click **"New Project"**
3. Fill in:
   - **Name**: `qsnews` (or your choice)
   - **Database Password**: Create a strong password and **SAVE IT**
   - **Region**: Choose closest to you (e.g., `us-east-1`)
4. Click **"Create new project"**
5. Wait 2-3 minutes for provisioning

### Step 2: Get Your Database Connection String

1. In your Supabase project dashboard, go to **Settings** → **Database**
2. Scroll to **Connection String** section
3. Select **"URI"** tab
4. Copy the connection string, it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
5. **Replace `[YOUR-PASSWORD]`** with your actual database password

### Step 3: Run the Migration SQL

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New query"**
3. Open the file `supabase_migration.sql` from your project
4. Copy and paste the entire SQL script
5. Click **"Run"** or press `Ctrl+Enter`
6. Verify success - you should see "Success. No rows returned"

### Step 4: Configure Local Environment

Add these to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
USE_SUPABASE=false  # Keep false for now during testing
```

**Replace**:
- `[YOUR-PASSWORD]` - Your Supabase database password
- `[YOUR-PROJECT-REF]` - Your project reference (from the URL)

### Step 5: Install PostgreSQL Driver

```bash
pip install psycopg2-binary
```

Or reinstall all requirements:

```bash
pip install -r requirements.txt
```

### Step 6: Run the Migration Script

This will copy all data from SQLite to Supabase:

```bash
python migrate_to_supabase.py
```

You'll see:
- Categories migrated
- Industries migrated
- Articles migrated
- Newsletters migrated

### Step 7: Test Supabase Connection

Update your `.env`:

```bash
USE_SUPABASE=true  # Switch to Supabase
```

Test it:

```bash
python src/main.py init-db
```

You should see: "Database engine created: Supabase PostgreSQL"

### Step 8: Update GitHub Actions

Add this secret to your GitHub repository:

**Go to**: `https://github.com/YOUR-USERNAME/QSNews/settings/secrets/actions`

**Add secret**:
```
Name: SUPABASE_DB_URL
Value: postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

### Step 9: Update GitHub Workflows

Add environment variable to your workflows (`.github/workflows/*.yml`):

```yaml
- name: Fetch newsletters from Gmail
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    NEWSLETTER_GMAIL: ${{ secrets.NEWSLETTER_GMAIL }}
    NEWSLETTER_PASS: ${{ secrets.NEWSLETTER_PASS }}
    SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
    USE_SUPABASE: true  # Enable Supabase in CI
  run: |
    python src/main.py fetch-newsletters
```

## 🔄 Switching Between SQLite and Supabase

### Use SQLite (Local Development)
```bash
# In .env
USE_SUPABASE=false
```

### Use Supabase (Production/Cloud)
```bash
# In .env
USE_SUPABASE=true
SUPABASE_DB_URL=postgresql://postgres:...
```

## 🎨 Supabase Features You Can Use

### 1. **Row Level Security (RLS)**
Already enabled in migration! Adjust policies in `supabase_migration.sql` as needed.

### 2. **Realtime Subscriptions**
```python
# Listen to database changes in real-time
supabase.table('articles').on('INSERT', handle_new_article).subscribe()
```

### 3. **Database Backups**
Automatic daily backups (7 days retention on free tier)

### 4. **API Auto-generated**
Access your data via REST API:
```
https://[YOUR-PROJECT-REF].supabase.co/rest/v1/articles
```

### 5. **Dashboard UI**
View and edit data directly in Supabase dashboard: **Table Editor**

## 🐛 Troubleshooting

### Error: "Could not connect to server"
- Check your database password
- Verify the connection string format
- Ensure your IP isn't blocked (Supabase allows all IPs by default)

### Error: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Error: "relation 'articles' does not exist"
- Run the SQL migration script first in Supabase SQL Editor
- Check you ran `supabase_migration.sql` completely

### Slow Performance
- Add indexes (already included in migration)
- Use connection pooling (already configured)
- Check your query patterns

## 📊 Verify Migration

Check counts match:

**SQLite:**
```bash
USE_SUPABASE=false python check_database.py
```

**Supabase:**
```bash
USE_SUPABASE=true python check_database.py
```

Or check in Supabase dashboard: **Table Editor** → see row counts

## 🎉 Benefits of Supabase

✅ **No SQLite file conflicts** - Multiple processes can access simultaneously  
✅ **Better performance** - PostgreSQL is faster for complex queries  
✅ **Scalable** - Handles more data and concurrent connections  
✅ **Built-in backups** - Automatic daily backups  
✅ **Real-time features** - Subscribe to database changes  
✅ **Web dashboard** - View/edit data visually  
✅ **Free tier** - 500MB database, 2GB transfer/month  

## 🔐 Security Best Practices

1. **Never commit** `.env` file (already in `.gitignore`)
2. **Use GitHub Secrets** for CI/CD (not plain text in workflows)
3. **Rotate passwords** periodically
4. **Enable RLS** policies for sensitive data
5. **Use service role key** only in backend (never expose to frontend)

## 📞 Need Help?

- Supabase Docs: https://supabase.com/docs
- Supabase Discord: https://discord.supabase.com
- GitHub Issues: Open an issue in your repo

---

Made with ❤️ for QSNews

