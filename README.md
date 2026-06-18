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

### Graph Model

The platform models the trading ecosystem as a directed graph.

* Users are represented as nodes.
* Wants are represented as directed edges.
* An edge `A → B` means User A wants an item owned by User B.

Example:

```text
A → B
```

A cycle in the graph represents a valid multi-party trade opportunity.

Example:

```text
A → B → C → A
```

### Cycle Detection Engine

The platform uses **Depth First Search (DFS)** to discover trade cycles.

Current capabilities:

* Variable-length cycle detection
* Configurable maximum cycle depth
* Cycle deduplication
* Self-loop prevention
* User-specific cycle discovery

---

## Features

### Authentication & Authorization

* JWT Authentication
* Refresh Token Support
* Role-Based Access Control (RBAC)
* Protected API Endpoints

### Item Management

* Create Items
* Retrieve Items
* Update Items
* Delete Items
* UUID-Based Public Identifiers

### Want Management

* Create Wants
* Update Wants
* Delete Wants
* Duplicate Want Prevention
* Self-Want Prevention

### Trading Engine

* Direct Trade Discovery
* Multi-Party Trade Cycle Detection
* User-Specific Cycle Recommendations

### Platform Features

* OpenAPI / Swagger Documentation
* Pagination Support
* Automated Test Suite
* Service-Layer Architecture

---

## Tech Stack

### Backend

* Python
* Django
* Django REST Framework

### Authentication

* SimpleJWT

### API Documentation

* drf-spectacular
* Swagger UI

### Database

* PostgreSQL Ready
* SQLite (Development)

### Testing

* Django Test Framework

---

## API Endpoints

### Authentication

| Method | Endpoint             |
| ------ | -------------------- |
| POST   | `/api/auth/login/`   |
| POST   | `/api/auth/refresh/` |

### Items

| Method | Endpoint             |
| ------ | -------------------- |
| GET    | `/api/items/`        |
| POST   | `/api/items/`        |
| GET    | `/api/items/{uuid}/` |
| PATCH  | `/api/items/{uuid}/` |
| DELETE | `/api/items/{uuid}/` |

### Wants

| Method | Endpoint             |
| ------ | -------------------- |
| GET    | `/api/wants/`        |
| POST   | `/api/wants/`        |
| GET    | `/api/wants/{uuid}/` |
| PATCH  | `/api/wants/{uuid}/` |
| DELETE | `/api/wants/{uuid}/` |

### Trading

| Method | Endpoint              |
| ------ | --------------------- |
| GET    | `/api/trades/direct/` |
| GET    | `/api/trades/cycles/` |

---

## Testing

Current automated test coverage includes:

* Cycle Detection Tests
* Item API Tests
* Want API Tests

Total Tests: **19**

Run the test suite:

```bash
python manage.py test
```

---

## Future Enhancements

* Trade Proposal Workflow
* Trade Acceptance Workflow
* Trade Execution Engine
* Database Transactions
* Trade History
* Caching
* Background Jobs
* Advanced Matching Algorithms

---

## Project Status

Current Version: MVP

Implemented:

* Authentication & Authorization
* Item Management
* Want Management
* Direct Trade Matching
* Multi-Party Cycle Detection
* UUID-Based Public Identifiers
* Pagination
* Automated Testing

Planned:

* Trade Execution Workflow
* Reservation System
* Transaction Management
* Performance Optimizations
