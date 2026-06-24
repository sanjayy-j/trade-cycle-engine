# Trade Cycle Engine

A graph-based multi-party trade matching platform that enables direct and cyclic item exchanges using DFS-powered cycle detection.

Traditional barter systems fail because of the **double coincidence of wants problem** - the person who owns the item you want may not want anything you own in return.

Trade Cycle Engine solves this by modeling users and their interests as a directed graph and discovering direct and multi-party trade opportunities that would otherwise be impossible.

---

## Problem Statement

Consider the following scenario:

* User A wants an item from User B.
* User B wants an item from User C.
* User C wants an item from User A.

No direct trade is possible, even though every participant could be satisfied through a coordinated exchange.

Trade Cycle Engine identifies these opportunities automatically by constructing a trade graph and detecting valid exchange cycles.

---

## Example Trade Cycle

Trade Graph:

```text
A → B → C → A
```

| User | Gives    | Receives |
| ---- | -------- | -------- |
| A    | Book     | Monitor  |
| B    | Monitor  | Keyboard |
| C    | Keyboard | Mouse    |

All participants receive a desired item through a single coordinated trade cycle.

---

## System Architecture

See [architecture.md](architecture.md) for a full breakdown of the layered architecture (views/serializers/services/models), the trade proposal lifecycle, and the concurrency model.

### Graph Model

The platform models the trading ecosystem as a directed graph.

* Users are represented as nodes.
* Wants are represented as directed edges.
* An edge `A → B` means User A wants an item owned by User B.

A cycle in the graph represents a valid multi-party trade opportunity, e.g. `A → B → C → A`.

### Cycle Detection Engine

The platform uses **Depth First Search (DFS)** to discover trade cycles.

Current capabilities:

* Variable-length cycle detection (configurable `MAX_CYCLE_LENGTH`)
* Cycle deduplication, both within a single detection run and against
  already-persisted active cycles
* Self-loop prevention
* User-specific cycle discovery

---

## Features

### Authentication & Authorization

* JWT Authentication (access + refresh tokens)
* Role-Based Access Control (RBAC)
* Object-level ownership/participant checks on every protected endpoint

### Item Management

* Create, retrieve, update, delete items
* UUID-based public identifiers
* Item lifecycle states: `AVAILABLE` → `RESERVED` → `TRADED`

### Want Management

* Create, update, delete wants
* Duplicate-want and self-want prevention

### Trading Engine

* Direct trade discovery
* Multi-party trade cycle detection and persistence
* User-specific cycle recommendations

### Trade Proposal Lifecycle

* Multi-party proposal creation with strict participant validation
  (every giver/receiver must be a proposal participant)
* Item reservation on proposal creation (`AVAILABLE` → `RESERVED`),
  preventing the same item from being double-booked across proposals
* Unanimous acceptance triggers atomic execution (ownership transfer,
  `RESERVED` → `TRADED`)
* Any participant can reject a pending proposal, releasing its
  reserved items back to `AVAILABLE`
* Proposals that go unanswered past their `expires_at` are lazily
  expired (on next read/accept/reject), also releasing reserved items
* Trade execution record + history per user

### Concurrency Protection

* `select_for_update()` row locking on items during proposal creation
  and execution closes the race window for double-spending the same
  item across concurrent requests
* Verified with a real multi-threaded test against PostgreSQL
  (see `exchange/tests/test_concurrency.py`)

### Platform Features

* OpenAPI / Swagger documentation (`/api/docs/`)
* Pagination
* Rate limiting (per-action DRF throttles)
* Structured logging (console, environment-aware verbosity)
* `/health/` and `/version/` endpoints for ops/monitoring
* Service-layer architecture; views stay thin

---

## Tech Stack

### Backend

* Python 3.12
* Django 6
* Django REST Framework

### Authentication

* SimpleJWT

### API Documentation

* drf-spectacular / Swagger UI

### Database

* PostgreSQL

### Testing

* Django Test Framework (71 tests, including a real multi-threaded
  concurrency test)

### Deployment

* Docker / docker-compose (app + PostgreSQL)
* GitHub Actions CI (migrate + test on every push/PR)

---

## Project Layout

```text
exchange/
├── views/          # auth_views, item_views, want_views, trade_views, proposal_views, system_views
├── serializers/     # item_serializers, want_serializers, trade_serializers
├── services/         # cycle_services, trade_services (business logic, transactions)
├── exceptions/      # domain exceptions (ItemNotAvailableError, ProposalNotPendingError)
├── models.py
├── permissions.py
├── throttles.py
└── tests/

tradecycle/
├── settings/        # base.py, development.py, production.py
├── urls.py
├── wsgi.py
└── asgi.py
```

---

## Local Setup

1. Copy `.env.example` to `.env` and fill in real values.
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Run the dev server: `python manage.py runserver`
5. Run tests: `python manage.py test`

By default `DJANGO_ENV` is unset, which uses `tradecycle/settings/development.py`
(relaxed security settings, convenient defaults). Set `DJANGO_ENV=production`
to use `tradecycle/settings/production.py`, which fails fast at import time
if `SECRET_KEY` or `ALLOWED_HOSTS` aren't configured, and enforces
HTTPS-only cookies/HSTS.

## Running with Docker

```bash
docker compose up --build
```

This starts a PostgreSQL container and the Django app (migrating
automatically on startup), exposed on `http://localhost:8000`.

---

## API Endpoints

### Authentication

| Method | Endpoint             |
| ------ | --------------------- |
| POST   | `/api/auth/login/`    |
| POST   | `/api/auth/refresh/`  |

### Items

| Method | Endpoint             |
| ------ | --------------------- |
| GET    | `/api/items/`         |
| POST   | `/api/items/`         |
| GET    | `/api/items/{uuid}/`  |
| PATCH  | `/api/items/{uuid}/`  |
| DELETE | `/api/items/{uuid}/`  |

### Wants

| Method | Endpoint              |
| ------ | ---------------------- |
| GET    | `/api/wants/`          |
| POST   | `/api/wants/`          |
| GET    | `/api/wants/{uuid}/`   |
| PATCH  | `/api/wants/{uuid}/`   |
| DELETE | `/api/wants/{uuid}/`   |

### Trading

| Method | Endpoint               |
| ------ | ----------------------- |
| GET    | `/api/matches/`         |
| GET    | `/api/trades/direct/`   |
| GET    | `/api/trades/cycles/`   |
| GET    | `/api/trade-history/`   |

### Trade Proposals

| Method | Endpoint                                     |
| ------ | --------------------------------------------- |
| GET    | `/api/trade-proposals/`                       |
| POST   | `/api/trade-proposals/`                       |
| GET    | `/api/trade-proposals/{uuid}/`                |
| POST   | `/api/trade-proposals/{uuid}/accept/`         |
| POST   | `/api/trade-proposals/{uuid}/reject/`         |

### Ops

| Method | Endpoint     |
| ------ | ------------- |
| GET    | `/health/`    |
| GET    | `/version/`   |

---

## Testing

Current automated test coverage includes:

* Cycle detection tests (incl. persistence dedup)
* Item API tests
* Want API tests
* Trade proposal tests (creation, participant validation, reservation)
* Trade proposal lifecycle tests (accept, reject, expiration)
* Trade execution / history tests
* Throttling tests
* Concurrency tests (real multi-threaded row-locking test)
* System endpoint tests (health, version)
* Serializer validation tests

Total Tests: **71**

Run the test suite:

```bash
python manage.py test
```

---

## Project Status

Current Version: **1.0.0 release candidate**

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the detailed feature/status
breakdown and known limitations.
