# Database migrations

`0001_platform_runtime.sql` creates the PostgreSQL tables used by the active API repository. It preserves the API's string account and content IDs and is safe to run more than once.

The migration also creates `platform_moderation_reports`, which backs the administrator moderation queue.

Apply it with PostgreSQL tooling:

```powershell
psql "$env:DATABASE_URL" -f backend/data_management/migrations/0001_platform_runtime.sql
```

For local development, `python -m data_management` also creates the SQLAlchemy metadata when `DB_AUTO_CREATE=true`.