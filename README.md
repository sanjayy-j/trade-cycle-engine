# Trade Cycle Engine

Trade Cycle Engine is a multi-user barter trading platform. Users list items
they own and items they want; the platform finds direct trades and
multi-party trade cycles between users automatically.

Traditional barter fails because of the **double coincidence of wants
problem** — the person who owns the item you want may not want anything you
own in return. Trade Cycle Engine solves this by modeling users and their
wants as a directed graph and searching it for valid exchange cycles.

```text
A wants B's item, B wants C's item, C wants A's item:

A → B → C → A
```

No direct trade is possible between any two of them, but all three can
trade simultaneously through a single coordinated cycle.

---

## Features

- JWT Authentication (access + refresh tokens)
- User Registration
- Role-Based Access Control (RBAC)
- Item Management (CRUD, with ownership enforcement)
- Soft Delete for Items (rows are kept so historical trades stay intact)
- Want Lists (with self-want and duplicate-want prevention)
- Direct Trade Matching
- Trade Cycle Detection (DFS-based, variable length, deduplicated)
- Trade Proposals (multi-party, with participant validation)
- Proposal Acceptance / Rejection
- Item Reservation System (`AVAILABLE` → `RESERVED` → `TRADED`)
- Trade Execution (atomic, transaction-safe)
- Trade History
- Rate Limiting (per-action throttles)
- Swagger / OpenAPI Documentation

---

## Technology Stack

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- JWT (`djangorestframework-simplejwt`)
- drf-spectacular (OpenAPI schema + Swagger UI)
- Docker / docker-compose (optional)
- Postman (manual API testing)

---

## Project Structure

```text
exchange/
├── views/          # auth_views, item_views, want_views, trade_views, proposal_views, system_views
├── serializers/    # auth_serializers, item_serializers, want_serializers, trade_serializers
├── services/       # cycle_services, trade_services - business logic and transactions
├── exceptions/     # domain exceptions (ItemNotAvailableError, ProposalNotPendingError)
├── models.py
├── permissions.py
├── pagination.py
├── throttles.py
├── constants.py
└── tests/

tradecycle/
├── settings.py     # single settings module, DEBUG-driven
├── urls.py
├── wsgi.py
└── asgi.py
```

See [architecture.md](architecture.md) for how the layers fit together and
how the trade proposal lifecycle and cycle detection actually work.

---

## Installation

1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in real values (database
   credentials, `SECRET_KEY`, etc.).
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Run the development server:
   ```bash
   python manage.py runserver
   ```

`DEBUG` defaults to `True` for local development (relaxed cookie/HTTPS
settings). Set `DEBUG=False` in production — this also requires `SECRET_KEY`
and `ALLOWED_HOSTS` to be set, and turns on strict cookies/HSTS.

### Running with Docker

```bash
docker compose up --build
```

This starts a PostgreSQL container and the Django app (migrating
automatically on startup), exposed on `http://localhost:8000`.

### Continuous Integration

GitHub Actions (`.github/workflows/ci.yml`) runs `pip install -r
requirements.txt`, `manage.py migrate`, and the full test suite against a
Postgres service container on every push/PR to `main`. This pipeline is
verified green against a from-scratch virtualenv + database as part of
this project's v1.0 ship pass.

---

## API Overview

| Area            | Endpoint                                | Methods                 |
| ---------------- | ---------------------------------------- | ------------------------ |
| Auth              | `/api/auth/register/`                    | POST                      |
| Auth              | `/api/auth/login/`                       | POST                      |
| Auth              | `/api/auth/refresh/`                     | POST                      |
| Items             | `/api/items/`                            | GET, POST                 |
| Items             | `/api/items/{uuid}/`                     | GET, PATCH, DELETE        |
| Wants             | `/api/wants/`                            | GET, POST                 |
| Wants             | `/api/wants/{uuid}/`                     | GET, PATCH, DELETE        |
| Matching          | `/api/matches/`                          | GET                        |
| Matching          | `/api/trades/direct/`                    | GET                        |
| Matching          | `/api/trades/cycles/`                    | GET                        |
| Trade Proposals   | `/api/trade-proposals/`                  | GET, POST                 |
| Trade Proposals   | `/api/trade-proposals/{uuid}/`           | GET                        |
| Trade Proposals   | `/api/trade-proposals/{uuid}/accept/`    | POST                       |
| Trade Proposals   | `/api/trade-proposals/{uuid}/reject/`    | POST                       |
| History           | `/api/trade-history/`                    | GET                        |
| Ops               | `/health/`, `/version/`                  | GET                        |
| Docs              | `/api/docs/`, `/api/schema/`             | GET                        |

Full interactive documentation is available at `/api/docs/` once the server
is running.

---

## End-to-End Workflow

1. **Register users** — `POST /api/auth/register/`
2. **Login** — `POST /api/auth/login/` to get a JWT access/refresh pair
3. **Create items** — `POST /api/items/` for each item a user owns
   (deleting an item later soft-deletes it — `DELETE /api/items/{uuid}/`
   removes it from listings/matching but keeps the row for trade history;
   an item currently `RESERVED` by a pending proposal cannot be deleted
   until that proposal is accepted, rejected, or expires)
4. **Create wants** — `POST /api/wants/` for items a user wants from others
5. **Find matches** — `GET /api/trades/direct/` (direct swaps) or
   `GET /api/trades/cycles/` (multi-party cycles)
6. **Create a proposal** — `POST /api/trade-proposals/` listing every
   participant and giver/receiver/item leg
7. **Accept or reject** — each participant calls `accept/` or `reject/`
8. **Trade executes automatically** once every participant has accepted —
   item ownership transfers and the items are marked `TRADED`

---

## Testing

```bash
python manage.py test
```

The suite is intentionally kept small and high-signal: it covers
authentication, authorization, the full proposal lifecycle, reservation
integrity, concurrency-safe locking, and cycle detection/deduplication
rather than every field-validation edge case. See
[PROJECT_STATUS.md](PROJECT_STATUS.md) for the current test count and
[architecture.md](architecture.md) for the concurrency model the
concurrency test exercises.

---

## Project Status

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for completed work, in-progress
items, and known limitations.
