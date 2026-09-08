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

## Amazon affiliate preview

The backend has a provider-neutral affiliate offer service with an Amazon-first API. It lets a creator attach a direct Amazon product link to their own post, returns safe product-card data in the feed, records a click when a viewer chooses the product, and keeps order and commission totals at zero until a retailer report confirms a qualifying purchase.

The service is intentionally in preview mode by default. It strips all creator-supplied query parameters, accepts only direct HTTPS Amazon product-detail URLs, and never exposes the stored destination URL in feed responses.

To configure an approved Amazon Associates deployment:

1. Register and obtain approval for the Golt mobile app in the applicable Amazon Associates marketplace.
2. Set `APP_ENV=production`.
3. Set `AMAZON_ASSOCIATES_TAGS` to comma-separated marketplace and tracking-ID pairs, such as `amazon.es=golt-21`.
4. Set `AFFILIATE_OUTBOUND_ENABLED=true` only after the app, disclosure, and link behavior have passed the program review.

Production refuses to open affiliate destinations unless both the feature flag and a tracking ID for that marketplace exist. The current click log is in memory. It does not activate database persistence, import Amazon orders, or create creator wallet credit.

Relevant routes:

- `POST /content/{content_id}/affiliate-links`
- `GET /content/{content_id}/affiliate-links`
- `POST /affiliate-links/{offer_id}/open`
- `GET /content/{content_id}/affiliate-attribution`
