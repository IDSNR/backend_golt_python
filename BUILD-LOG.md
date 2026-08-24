# BUILD-LOG

## 2026-08-24 — Security and Phase A foundation fixes

- Replaced deterministic Bearer-as-user-id behavior with random server-side sessions that expire after seven days and support logout revocation. The explicit `X-User-Id` path remains available for local development compatibility; production Bearer tokens must be issued sessions.
- Enforced authenticated actors on reports, referrals, legacy social follows, and follow-request approval; aligned the legacy social route with the shared social service.
- Added private-profile filtering to aggregate feeds and active stories, plus 24-hour story expiration metadata and filtering.
- Hardened media upload with authenticated ownership, allowlisted image/video MIME types, a 50 MB size limit, collision-resistant filenames, and original filename metadata.
- Added authenticated group/community APIs for creation, discovery, public/private membership, owner approval, and leaving groups.
- Added SecureStore-backed mobile session restoration, logout, and session cleanup in `mobile-app/App.tsx`.
- Updated tests for the authenticated contracts and added group coverage. PostgreSQL persistence, real OAuth provider verification, and production object storage remain infrastructure/provider-dependent follow-up work.

## 2026-07-28

- Scaffolded a FastAPI-based Python backend alongside the existing Node.js backend.
- Added a dedicated project structure under backend-python with app/, tests/, and supporting config files.
- Implemented initial health, profile, wallet, and content routes.
- Added service-layer modules for auth, wallet, and content to keep business logic separate from HTTP handlers.
- Added pytest-based tests for the newly ported endpoints.
- Verified the Python backend test suite successfully.

## 2026-08-24

- Added a versioned roulette probability engine with a four-prize launch distribution: EUR 200 (0.01%), EUR 2 (1%), customizable hat (49.495%), and collectable (49.495%). Visual sectors remain equal while outcome odds are skewed server-side.
- Updated the roulette API to select outcomes from server-owned probabilities and to accept profile/bot-score metadata as explicit future policy signals without trusting client input.
- Added `roulette_decisions` audit records containing engine version, normalized distribution, draw, and decision signals for later review and model replacement.
- Wired the mobile roulette wheel to display the real odds, render four equal visual sectors, and animate toward the server-selected sector.
- Kept the existing `sessionId`, `options`, and `prize` response fields compatible for downstream clients.
