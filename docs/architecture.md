# Trade Cycle Engine — Architecture Overview

## Purpose

This document describes the core domain model, service-layer architecture, execution workflow, and production-oriented design decisions used in the Trade Cycle Engine backend.

---

# System Overview

Trade Cycle Engine is a graph-based barter trading platform that allows users to:

- List items for exchange.
- Express interest in other users' items.
- Discover direct trades.
- Detect multi-party trade cycles.
- Create trade proposals.
- Collect participant approvals.
- Execute ownership transfers.
- Maintain trade history.

The system follows a layered architecture:

- API Layer (Views)
- Serialization Layer
- Service Layer
- Domain Models
- Database

---

# Domain Model

## User

Extends Django's `AbstractUser`.

### Fields

- username
- password
- role

### Roles

- ADMIN
- USER

### Relationships

- owns Items
- creates Wants
- participates in TradeProposals
- participates in TradeCycles

---

## Item

Represents an item available for exchange.

### Fields

- owner (User)
- public_id (UUID)
- name
- description
- status
- created_at
- updated_at

### Statuses

- AVAILABLE
- RESERVED
- TRADED

---

## Want

Represents interest in another user's item.

### Fields

- user
- public_id
- item
- created_at

### Constraints

- One user cannot want the same item twice.
- Users cannot want their own items.

---

## TradeProposal

Represents a proposed multi-party trade.

### Fields

- public_id
- status
- created_at
- updated_at

### Statuses

- PENDING
- ACCEPTED
- REJECTED
- EXECUTED
- EXPIRED

### Relationships

- participants
- trade_items

---

## TradeParticipant

Represents a participant in a proposal.

### Fields

- proposal
- user
- accepted
- accepted_at

### Constraints

- One participant per proposal.

---

## TradeItem

Represents an item transfer within a proposal.

### Fields

- proposal
- giver
- receiver
- item
- created_at

### Constraints

- One item per proposal.

---

## TradeCycle

Stores detected trade cycles.

### Fields

- public_id
- active
- created_at
- expires_at

### Purpose

Allows cycle recommendations to be persisted rather than recalculated repeatedly.

---

## TradeCycleParticipant

Links users to cycles.

### Fields

- cycle
- user

---

## TradeCycleTrade

Stores the transfers inside a cycle.

### Fields

- cycle
- giver
- receiver
- item

---

## TradeExecution

Stores completed trade executions.

### Fields

- public_id
- proposal
- executed_at

### Purpose

Provides an immutable record of completed trades.

---

# Service Layer

Location:

```
exchange/services/
```

---

## cycle_services.py

### build_trade_graph()

Builds the trade graph using:

- Want.user
- Want.item
- Item.owner

Uses:

- select_related()
- prefetch_related()

Returns an adjacency list.

---

### find_cycles_for_user()

Performs depth-limited DFS.

Parameters:

- graph
- user_id
- max_depth

Returns:

- participants
- trades
- cycle length

---

### persist_trade_cycles()

Stores detected cycles.

Creates:

- TradeCycle
- TradeCycleParticipant
- TradeCycleTrade

Uses:

- transaction.atomic()
- bulk_create()

---

## trade_services.py

### create_trade_proposal()

Creates:

- TradeProposal
- TradeParticipant records
- TradeItem records

Uses:

- transaction.atomic()
- bulk_create()

---

### accept_trade_proposal()

- Locks participant rows.
- Marks participant accepted.
- Records acceptance timestamp.
- Executes trade after all approvals.

Uses:

- select_for_update()

---

### execute_trade_proposal()

Transfers:

- Item.owner
- Item.status

Updates:

- Proposal status

Creates:

- TradeExecution record

All operations occur inside a single transaction.

---

# API Architecture

## Item APIs

- GET /api/items/
- POST /api/items/
- PATCH /api/items/{id}/
- DELETE /api/items/{id}/

---

## Want APIs

- GET /api/wants/
- POST /api/wants/
- PATCH /api/wants/{id}/
- DELETE /api/wants/{id}/

---

## Matching APIs

- GET /api/matches/
- GET /api/trades/direct/
- GET /api/trades/cycles/

---

## Trade Proposal APIs

- GET /api/trade-proposals/
- POST /api/trade-proposals/
- GET /api/trade-proposals/{public_id}/
- POST /api/trade-proposals/{public_id}/accept/

---

## Trade History API

- GET /api/trade-history/

---

# Query Optimization

The project uses:

- select_related()
- prefetch_related()
- bulk_create()
- database indexing

### Indexed Fields

- Item.status
- Item.created_at
- TradeProposal.status
- TradeProposal.created_at

### Query Goals

- Avoid N+1 queries.
- Minimize database round trips.
- Reduce row-by-row inserts.

---

# Concurrency Protection

The system protects critical operations using:

- transaction.atomic()
- select_for_update()

This prevents:

- double acceptance
- inconsistent execution
- race conditions

---

# Rate Limiting

Custom DRF throttles protect expensive endpoints.

### TradeProposalThrottle

Limits proposal creation.

---

### TradeAcceptanceThrottle

Limits proposal acceptance attempts.

---

### CycleDetectionThrottle

Limits graph traversal requests.

---

# Testing Strategy

Tests are located in:

```
exchange/tests/
```

### Coverage

- Item APIs
- Want APIs
- Trade proposals
- Trade execution
- Trade history
- Cycle detection
- Throttling
- Permissions
- Authentication

Current test suite:

- 42+ automated tests
- All tests passing

---

# Design Principles

- Fat service layer, thin views.
- Business logic outside views.
- Atomic write operations.
- UUID-based public identifiers.
- RESTful APIs.
- Production-oriented query optimization.
- Test-driven validation of business logic.
- Separation of concerns.

---

# Future Enhancements

- Docker deployment
- CI/CD pipeline
- Redis caching
- Background jobs
- Monitoring and logging
- Production deployment infrastructure