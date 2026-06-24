# Trade Cycle Engine — Project Status

Current Version: **1.0.0 release candidate**

---

## Completed

### Core Platform
- Custom User model with role field (RBAC)
- JWT authentication (access + refresh)
- User registration (forces default `USER` role; no privilege-escalation path)
- UUID public identifiers on all resources
- Pagination
- PostgreSQL
- Swagger / OpenAPI documentation (`/api/docs/`)
- `/health/` and `/version/` ops endpoints

### Item & Want Management
- Item CRUD (owner-or-admin enforced on update/delete)
- Item soft delete: `DELETE /api/items/{uuid}/` sets `is_deleted`/
  `deleted_at` instead of removing the row, so `TradeItem`/`TradeExecution`
  records that reference the item keep resolving it. Soft-deleted items are
  excluded from listings, direct/cycle matching, and from being wanted or
  proposed (`Item.active` manager + restricted serializer querysets)
- `RESERVED` items cannot be deleted — `ItemViewSet.destroy` rejects the
  request with `400 {"error": "Reserved items cannot be deleted."}` rather
  than letting a pending proposal execute against a deleted item.
  `AVAILABLE` and `TRADED` items can still be deleted (soft-deleted) freely
- Want CRUD (self-want and duplicate-want prevention)
- Object-level authorization shared via `OwnerOrAdminActionsMixin`
- Item lifecycle states: `AVAILABLE` → `RESERVED` → `TRADED`

### Trade Matching Engine
- Direct trade matching (2-party mutual wants)
- Graph builder (`build_trade_graph`) over all `AVAILABLE`-item wants
- DFS-based cycle detection, variable length (`MAX_CYCLE_LENGTH`)
- User-specific cycle recommendations
- Cycle persistence with deduplication (repeated detection calls reuse an
  existing active `TradeCycle` instead of creating duplicates)

### Trade Proposal System
- `TradeProposal` / `TradeParticipant` / `TradeItem` models
- `expires_at` on every proposal (24h default)
- Proposal creation with participant validation (every giver/receiver must
  be a listed participant) enforced at the serializer layer
- Proposal listing / detail / accept / reject endpoints
- Unanimous acceptance triggers atomic execution
- Any participant can reject a pending proposal, releasing reserved items
- Lazy expiration: a proposal past `expires_at` is flipped to `EXPIRED` (and
  its items released) the next time it is read, accepted, or rejected

### Trade Execution & Concurrency
- Atomic, transaction-wrapped execution service
- Item reservation on proposal creation, preventing the same item from being
  double-booked across concurrent proposals
- `select_for_update()` row locking (ordered by id) during both reservation
  and execution, verified with a real multi-threaded test against Postgres
- Ownership transfer + item status updates on execution
- Trade execution records + per-user trade history

### Architecture
- `exchange/views/`, `exchange/serializers/` split into per-domain modules
- `exchange/services/` holds all business logic and transactions; views stay
  thin and translate domain exceptions into HTTP status codes
- `exchange/exceptions/` for domain-specific errors
- Single `tradecycle/settings.py`, environment-driven via `DEBUG` (no
  settings package, no environment-switching indirection)
- Query optimization (`select_related` / `prefetch_related` throughout)
- Bulk database operations, database indexing on hot lookup fields

### Production Readiness
- Per-action API rate limiting (DRF throttles)
- Structured logging (console handler, `DEBUG`-aware verbosity)
- `ALLOWED_HOSTS` / secure cookie / HSTS settings, gated on `DEBUG`
- Fails fast (`ImproperlyConfigured`) if `SECRET_KEY` or `ALLOWED_HOSTS`
  aren't set when `DEBUG=False`
- Dockerfile + docker-compose (app + PostgreSQL)
- GitHub Actions CI (migrate + full test suite on every push/PR), verified
  green from a from-scratch virtualenv + Postgres container. A prior CI
  failure was traced to `requirements.txt` having been saved as UTF-16
  (every existing local venv had already installed the correct packages
  before that, so the breakage was invisible locally and only surfaced on
  a fresh CI runner's `pip install`); the file is now plain UTF-8

### Testing
- 37 automated tests, consolidated to high-signal coverage:
  - Authentication (registration, login, refresh, role defaulting, registration throttling)
  - Authorization (ownership enforcement, non-participant rejection)
  - Item & want CRUD and validation rules
  - Item soft delete (row survives, excluded from listings, blocks wanting/proposing)
  - Reserved-item delete protection (reserved blocked, available/traded allowed)
  - Trade proposal lifecycle (create, participant validation, accept,
    reject, execution, ownership transfer)
  - Reservation/release integrity
  - Concurrency (real multi-threaded row-locking test against Postgres)
  - Cycle detection and duplicate-cycle prevention
  - Historical trade record integrity after the underlying item is deleted

---

## In Progress

Nothing is currently mid-implementation; the items below are the next
planned increments (see Future Improvements).

---

## Known Limitations

- **No automated expiry sweep.** Expiration is lazy (checked only when a
  specific proposal is read/accepted/rejected); an abandoned proposal stays
  `PENDING` with its items `RESERVED` until something touches it.
- **No Redis/cache layer.** Cycle detection rebuilds the full want graph on
  every request; acceptable at current scale.
- **No background job queue.** All work (including cycle detection) runs
  synchronously within the request/response cycle.

---

## Future Improvements

- **Background job for proposal expiry.** A periodic management command or
  task queue (e.g. Celery beat) would expire abandoned proposals and release
  their items without requiring a request to that specific proposal.
- **Redis cache.** Cache the want graph (or detected cycles) once it grows
  large enough that rebuilding it per-request becomes measurable.
- **Email verification.** Registration currently activates accounts
  immediately with no email confirmation step.
- **Notifications.** No notification mechanism exists for proposal
  creation, acceptance, rejection, or execution — participants must poll.
- **Admin dashboard.** Administration is currently limited to the default
  Django admin (`User`, `Item`, `Want` registered) with no custom tooling
  for moderating trades, proposals, or reviewing soft-deleted items.

---

## Current Metrics

- 37 automated tests, all passing
- Single-file settings module, `DEBUG`-driven
- CI verified green from a from-scratch virtualenv + Postgres container
- Dockerized, with CI running migrations + the full test suite on every
  push/PR
