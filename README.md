# PartnerHub Python backend

This directory contains a FastAPI-based Python port of the existing Node/Express backend.
It is intentionally scaffolded to mirror the current API shape so it can be evolved incrementally.

## Quick start

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - CMD: `.venv\Scripts\activate.bat`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Configure the local database:
   - Copy `.env.example` to `.env`.
   - Set `DATABASE_URL` to the Postgres database running on this machine.
   - Set `PERSISTENCE_ENABLED=true` so active account, profile, content, follow, and engagement services use PostgreSQL.
   - Run `python -m data_management` once to create missing SQLAlchemy tables.
   - Set `DB_AUTO_CREATE=true` only if you want API startup to create missing tables automatically.
5. Check the database connection:
   `curl http://localhost:8000/health/database`
6. Run the API:
   `uvicorn app.main:app --reload --port 8000`

The `.env` file is ignored by git. Do not commit the password or connection string.

When `PERSISTENCE_ENABLED=true`, initialize the schema before starting the API. The active API repository uses the string-ID tables in `data_management/migrations/0001_platform_runtime.sql`. The older normalized SQLAlchemy models remain available for the wallet/metadata expansion and are also created by the Python initializer.
