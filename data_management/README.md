# data_management

This package provides a reusable SQLAlchemy-based data integration layer for the PartnerHub project.

## What it provides

- PostgreSQL connection setup via SQLAlchemy
- Database initialization helpers
- A social-media-oriented relational schema:
  - accounts and authentication identities
  - user profiles with biography and direct links
  - metadata storage for flexible account settings
  - wallet balances and ledger entries
  - follows, blocks, circles, and circle memberships
  - posts, comments, likes, bookmarks, and stories
  - direct messages and message threads
  - notifications and reports

## Suggested environment variables

Set these before running:

```bash
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/golt
export PERSISTENCE_ENABLED=true
```

## Basic usage

```python
from data_management import init_db, create_account_and_profile, update_user_profile

init_db()

account = create_account_and_profile(
    username="alex",
    email="alex@example.com",
    display_name="Alex",
    auth_provider="email",
    password_hash="hashed-password",
    biography="Product designer and creator",
    website_url="https://example.com",
)

update_user_profile(
    account_id=account.id,
    biography="Updated bio",
    website_url="https://newsite.com",
)
```

The active API services use `data_management.repositories.repository` when `PERSISTENCE_ENABLED=true`. This repository persists accounts, profiles, posts, follows, likes, bookmarks, shares, and comments in the `platform_*` tables. With persistence disabled, the existing in-memory development fallback remains available for isolated tests.

## Core functions

- create_account_and_profile(...)
  - Creates an account, user profile, default balance, and authentication identity.

- get_account_by_id(account_id)
- get_account_by_username(username)
- get_account_by_email(email)

- update_user_profile(...)
  - Updates biography, website URL, location, pronouns, avatar URL, and banner URL.

- set_user_metadata(account_id, key, value, value_type="string")
- retrieve_user_metadata(account_id, key=None)
  - Stores and retrieves flexible account metadata.

- create_post(...)
- create_story(...)
- follow_account(follower_account_id, followed_account_id)
- create_circle(...)
- add_circle_member(circle_id, account_id, role="member")
- send_direct_message(...)

- get_user_balance(account_id)
- record_balance_entry(...)
  - Records wallet activity and updates balance.

## Relational structure overview

The schema is designed around a central Account entity and several feature-specific tables:

- accounts
  - primary identity record
- user_profiles
  - biography, website, avatar/banner details
- auth_identities
  - supports Google, email/password, and future providers such as Meta
- account_metadata
  - flexible per-account settings and flags
- account_balances and account_ledger_entries
  - wallet and transaction history
- follows and blocks
  - social graph relationships
- circles and circle_members
  - communities and groups
- posts / comments / likes / bookmarks
  - feed and engagement features
- stories
  - short-form content
- direct_message_threads / direct_message_thread_participants / direct_messages
  - private messaging
- notifications and reports
  - social platform operations and moderation

## Authentication design

The schema is provider-flexible:

- auth_provider can be set to email, google, meta, or any future provider.
- auth_identities stores one or more login methods per account.
- password_hash is optional, allowing provider-based accounts to coexist with email/password accounts.

This makes future expansion straightforward.

## Notes

- This module is meant to be importable and integration-friendly, not a full application runtime.
- The database schema is intentionally normalized enough for a modern social platform while remaining simple for early development.
- For production, add indexes, soft-delete support, rate limiting, and more advanced moderation workflows.
