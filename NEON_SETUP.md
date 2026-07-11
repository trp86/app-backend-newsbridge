# Neon Database Setup Guide

This guide walks you through setting up Neon serverless Postgres for Global Knowledge Brief.

## Why Neon?

- **Serverless**: Auto-scales and pauses when idle
- **Free tier**: Generous free tier for small projects
- **Fast**: Low latency with edge locations
- **Modern**: Built for modern cloud-native apps
- **Postgres**: Full PostgreSQL compatibility

## Step 1: Create Neon Account

1. Go to [https://neon.tech](https://neon.tech)
2. Sign up with GitHub/Google or email
3. Create a new project named `newsbridge` or similar

## Step 2: Get Database Connection String

1. In Neon dashboard, go to your project
2. Click **Connection Details**
3. Copy the connection string (it looks like):
   ```
   postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

## Step 3: Configure Application

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Neon connection string:
   ```env
   DATABASE_URL=postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

3. Keep other settings (Gemini API, Telegram) as needed

## Step 4: Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

This will install `psycopg[binary]` for Postgres support.

## Step 5: Initialize Database

Run the initialization script:

```bash
python backend/scripts/init_db.py
```

This creates all tables and indexes in your Neon database.

## Step 6: Verify Connection

Check database health:

```bash
python -c "from src.core.database import check_database_health; print(check_database_health())"
```

You should see counts for all tables (initially zeros).

## Step 7: Migrate Existing SQLite Data (Optional)

If you have existing data in SQLite that you want to migrate:

```bash
python backend/scripts/migrate_sqlite_to_neon.py
```

*(Note: Migration script needs to be created separately)*

## Switching Between SQLite and Postgres

The application automatically detects which database to use:

- **Postgres**: If `DATABASE_URL` is set in `.env`
- **SQLite**: If `DATABASE_URL` is empty (uses `DATABASE_PATH`)

To switch back to SQLite for local development:
1. Comment out or remove `DATABASE_URL` from `.env`
2. The app will use `data/brief.db` automatically

## Neon-Specific Features

### Connection Pooling
Neon handles connection pooling automatically. No additional configuration needed.

### Branching (Optional)
Neon supports database branching for testing:
```bash
# Create a branch for testing
neon branches create --name testing
```

### Monitoring
Check your database usage in Neon dashboard:
- Storage used
- Compute hours
- Active connections

## Troubleshooting

### Connection timeout
If you see timeout errors:
1. Check if your IP is allowed (Neon allows all by default)
2. Verify the connection string is correct
3. Ensure `sslmode=require` is in the connection string

### SSL errors
Make sure your connection string includes `?sslmode=require`

### Schema errors
If tables don't match expectations:
```bash
# Drop all tables and reinitialize
python backend/scripts/cleanup_database.py
python backend/scripts/init_db.py
```

## Cost Considerations

Neon Free Tier includes:
- 0.5 GB storage
- 100 hours compute/month
- Auto-scaling and auto-suspend

For Global Knowledge Brief (Phase 1 MVP):
- Estimated usage: ~50 MB storage
- Estimated compute: ~10 hours/month
- **Cost: FREE** ✅

## Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use environment variables** in production (Vercel, Railway, etc.)
3. **Rotate passwords** periodically
4. **Use read-only connections** for analytics queries (optional)

## Next Steps

Once Neon is set up:
1. Run your ingestion pipeline: `python backend/scripts/test_ingestion.py`
2. Test editorial flow: `python backend/scripts/test_editorial.py`
3. Deploy to production with Neon connection string in env vars

## Resources

- [Neon Documentation](https://neon.tech/docs)
- [Psycopg 3 Documentation](https://www.psycopg.org/psycopg3/docs/)
- [Connection String Format](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
