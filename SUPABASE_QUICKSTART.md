# 🚀 Supabase Quick Start

Since you already have your Supabase organization set up, here's the fastest path to get your database migrated:

## ⚡ 5-Minute Setup

### 1️⃣ Create Supabase Project (2 min)
```
1. Go to: https://supabase.com/dashboard
2. Click "New Project"
3. Name: qsnews
4. Database Password: [Create and SAVE it]
5. Region: us-east-1 (or closest)
6. Click "Create new project"
```

### 2️⃣ Run Migration SQL (1 min)
```
1. Supabase Dashboard → SQL Editor
2. Open: supabase_migration.sql
3. Copy + Paste entire file
4. Click "Run"
```

### 3️⃣ Add to .env (1 min)
```bash
# Add these lines to your .env file:
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
USE_SUPABASE=false  # Set to 'true' when ready to switch
```

Get connection string from: **Settings → Database → Connection String (URI)**

### 4️⃣ Install Driver (30 sec)
```bash
pip install psycopg2-binary
```

### 5️⃣ Migrate Data (30 sec)
```bash
python migrate_to_supabase.py
```

### 6️⃣ Test (30 sec)
```bash
# Switch to Supabase
# In .env: USE_SUPABASE=true

python src/main.py init-db
# Should see: "Database engine created: Supabase PostgreSQL"
```

### 7️⃣ Add GitHub Secret
```
Go to: https://github.com/AIK16520/QSNews/settings/secrets/actions
Add: SUPABASE_DB_URL
Value: Your connection string
```

## ✅ That's It!

Your database is now on Supabase!

### Switch Between Databases:

**Local SQLite** (development):
```bash
USE_SUPABASE=false  # in .env
```

**Supabase** (production):
```bash
USE_SUPABASE=true  # in .env
```

## 🎯 Next Actions

1. ✅ Keep SQLite for local dev
2. ✅ Use Supabase for GitHub Actions  
3. ✅ Update workflows to use `SUPABASE_DB_URL` secret
4. ✅ No more database file conflicts!

## 📚 Full Guide

See `SUPABASE_MIGRATION_GUIDE.md` for detailed explanations.

---

**Need help?** Check the migration guide or open an issue!

