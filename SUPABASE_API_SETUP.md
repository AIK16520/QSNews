# 🔄 Using Supabase API Instead of Direct Database Connection

Since the direct PostgreSQL connection has DNS issues, we're switching to use the Supabase API.

## ✅ What's Already Done

1. ✅ Migration script uses API (`migrate_to_supabase_api.py`)
2. ✅ Added `supabase` to requirements.txt
3. ✅ Created Supabase API wrapper (`database_supabase.py`)
4. ✅ Updated `config.py` to use `SUPABASE_URL` and `SUPABASE_KEY`

## 🔧 What You Need to Configure

### 1. Update Your `.env` File

```bash
# Remove or comment out:
# SUPABASE_DB_URL=postgresql://...

# Add these instead:
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-service-role-key
USE_SUPABASE=true
```

Get these from: **Supabase Dashboard → Settings → API**

### 2. Update GitHub Actions Secrets

Remove: `SUPABASE_DB_URL`

Add:
- `SUPABASE_URL` = `https://xxxxx.supabase.co`
- `SUPABASE_KEY` = your service role key

### 3. Update Streamlit Cloud Secrets

Go to **Settings → Secrets** and update:

```toml
OPENAI_API_KEY = "sk-..."
NEWSLETTER_GMAIL = "your@email.com"
NEWSLETTER_PASS = "your-app-password"

# Use API instead of database URL:
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-service-role-key"
USE_SUPABASE = "true"
```

## ⚠️ Known Limitations

The Supabase API wrapper provides basic functionality:
- ✅ Queries with `.filter_by()` and `.all()`
- ✅ Insert with `.add()` and `commit()`
- ✅ Count with `.count()`
- ⚠️  Complex queries may need adjustment
- ⚠️  Relationships (`.category`, `.industries`) won't lazy-load

## 🧪 Testing

Test the connection:

```bash
python -c "from src.utils.database import get_session; s = get_session(); print('Connected!'); s.close()"
```

Should print: "Using Supabase API" and "Connected!"

## 🐛 If You Get Errors

If specific queries don't work, you can:

1. **Use direct Supabase client**:
```python
from supabase import create_client
import config

client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
result = client.table('articles').select('*').limit(10).execute()
```

2. **Or switch back to SQLite for local dev**:
```bash
USE_SUPABASE=false  # in .env
```

## 📚 Supabase API Docs

- Python Client: https://supabase.com/docs/reference/python/introduction
- API Reference: https://supabase.com/docs/guides/api

---

**Note**: The app will work for most common operations. Complex dashboard features may need minor adjustments if they use advanced SQLAlchemy patterns.

