Trade Cycle Engine - Architecture Overview

Purpose
-------
This document describes the core domain model, service-layer architecture, and integration points for the Trade Cycle Engine backend.

Domain Model
------------
User
- owns Items
- creates Wants

Item
- fields: owner (User), public_id (UUID), name, description, status, created_at, updated_at
- statuses: AVAILABLE, RESERVED, TRADED

Want
- fields: user (User), public_id (UUID), item (Item), created_at
- creates an edge in the trade graph: user -> item.owner

TradeProposal
- fields: public_id, status, created_at, updated_at
- relationships: participants (TradeParticipant), trade_items (TradeItem)

TradeParticipant
- fields: proposal (TradeProposal), user (User), accepted (bool), accepted_at

TradeItem
- fields: proposal (TradeProposal), giver (User), receiver (User), item (Item), created_at

Service Layer
-------------
Location: `exchange/services/`

- `cycle_services.py`:
  - `build_trade_graph()` - builds adjacency list from all Wants (select_related user,item,item__owner)
  - `find_cycles_for_user(graph, user_id, max_depth)` - DFS-based cycle detection, returns structured cycles

- `trade_services.py`:
  - `create_trade_proposal(participants, trades)` - creates TradeProposal, TradeParticipant, and TradeItem records within `transaction.atomic()`
  - `accept_trade_proposal(proposal, user)` - marks participant accepted (uses `select_for_update()`), triggers execution when all accepted
  - `execute_trade_proposal(proposal)` - transfers `Item.owner` to `TradeItem.receiver`, marks item as `TRADED`, updates proposal status to `EXECUTED` (all inside `transaction.atomic()`)

Guidelines & Best Practices
--------------------------
- Services import models only (`from ..models import ...`). Do not import views or serializers in service modules.
- Expose services via `exchange/services/__init__.py` for cleaner imports like `from exchange.services import build_trade_graph`.
- Use `select_related`/`prefetch_related` to avoid N+1 queries.
- Use `select_for_update()` when modifying participant acceptance to avoid race conditions.

Import Changes
--------------
Update all existing imports referencing the old `exchange/services.py` to use the package:
- `from exchange.services import build_trade_graph, find_cycles_for_user`
- `from exchange.services import create_trade_proposal, accept_trade_proposal` (where needed)

Circular Dependency Risks
------------------------
- Risk: Importing views/serializers inside service modules leading to circular imports.
- Mitigation: Services only import `models` and standard libraries (transaction, timezone, etc.). Keep service functions independent of request/response types.

Migration & Test Notes
----------------------
- This refactor doesn't require DB migrations by itself. Changes to models (like earlier `public_id` additions) did require migrations.
- When adding new logic that mutates models (e.g., ownership transfer), add unit tests in `exchange/tests/` that exercise service functions directly.

