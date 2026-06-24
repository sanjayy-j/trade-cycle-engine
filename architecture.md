# Architecture

## Layers

```
HTTP request
   │
   ▼
views/            — auth dependency, request parsing, status codes. No business logic.
   │
   ▼
serializers/      — field validation, type coercion, cross-field rules
   │                 (e.g. "giver != receiver", "every giver/receiver is a participant")
   ▼
services/         — business logic, transactions, locking. The only layer
   │                 that touches more than one model write at a time.
   ▼
models/           — schema, simple model-local helpers (e.g. `is_expired()`)
```

Views never construct querysets that span multiple models' writes, and
services never know about HTTP — they raise plain Python exceptions
(`exchange/exceptions/`) that views translate into status codes. This
split is what let the trade-lifecycle work (reject/expire) land as new
service functions without touching a single view's URL, permission
class, or response shape for the existing accept/create/detail flows.

## Package layout

- `exchange/views/` — one module per resource family (`auth_views`,
  `item_views`, `want_views`, `trade_views`, `proposal_views`,
  `system_views`). `exchange/views/__init__.py` re-exports every public
  view so `exchange/urls.py` didn't need to change when the split
  happened.
- `exchange/serializers/` — mirrors the views split for the things that
  actually need their own serializer module (`item_serializers`,
  `want_serializers`, `trade_serializers`).
- `exchange/services/` — `cycle_services.py` (graph build, DFS, cycle
  persistence/dedup) and `trade_services.py` (proposal lifecycle:
  create, accept, reject, expire, execute).
- `exchange/exceptions/` — `ItemNotAvailableError`,
  `ProposalNotPendingError`. Services raise these; views catch them and
  map to `400`/`409`.
- `tradecycle/settings/` — `base.py` (everything environment-agnostic),
  `development.py` (relaxed security defaults), `production.py`
  (fail-fast validation + strict security settings). Selected via the
  `DJANGO_ENV` env var in `tradecycle/settings/__init__.py`.

## Trade proposal lifecycle

```
                 create_trade_proposal()
                          │
                          ▼
                    ┌──────────┐
        ┌──────────▶│ PENDING  │◀─────────────┐
        │           └────┬─────┘              │
        │     accept (all)│  reject (any)      │ time passes
        │                 │                    │ past expires_at
        ▼                 ▼                    ▼
  ┌───────────┐     ┌───────────┐        ┌───────────┐
  │ EXECUTED  │     │ REJECTED  │        │ EXPIRED   │
  └───────────┘     └───────────┘        └───────────┘
   items → TRADED    items → AVAILABLE    items → AVAILABLE
```

- **Reservation**: `create_trade_proposal` locks every referenced
  `Item` row (`select_for_update`, ordered by id), verifies all are
  `AVAILABLE`, then flips them to `RESERVED` — all inside one
  transaction. This is what makes the same item unable to be proposed
  in two proposals at once: the second caller either blocks on the lock
  and then sees `RESERVED`, or sees it directly and raises
  `ItemNotAvailableError`.
- **Accept**: each accept locks that participant's row, and once every
  participant has accepted, triggers `execute_trade_proposal` inside the
  same transaction.
- **Execute**: locks every affected `Item` row (again ordered by id, to
  avoid lock-ordering deadlocks against a concurrent reservation), then
  transfers ownership and marks them `TRADED`.
- **Reject**: any single participant can cancel the whole proposal.
  Locks the proposal row, checks it's still `PENDING`, flips to
  `REJECTED`, and releases its items back to `AVAILABLE`.
- **Expire**: lazy, not a background sweep. `expire_trade_proposal_if_needed`
  is called at the top of `accept_trade_proposal`, `reject_trade_proposal`,
  and `TradeProposalDetailView.get` — it locks the proposal, re-checks
  `is_expired()` under the lock, and if true, flips to `EXPIRED` and
  releases items. This means an abandoned proposal that nobody ever
  reads/accepts/rejects again stays `PENDING` (and its items stay
  `RESERVED`) until something touches it — see `PROJECT_STATUS.md` for
  why a periodic sweep is still a follow-up.

## Concurrency model

Two places need real locking, both via Postgres `SELECT ... FOR UPDATE`:

1. **Reservation race** (two proposals claiming the same item): tested
   for real in `exchange/tests/test_concurrency.py` using
   `TransactionTestCase` + two OS threads, each with their own DB
   connection, attempting `create_trade_proposal` on the same item.
   Exactly one succeeds; lock visibility across threads requires
   `TransactionTestCase` (not `TestCase`, which wraps each test in a
   single transaction that both threads would otherwise share).
2. **Execution race** (two trades touching the same item at execution
   time): closed by locking `Item` rows inside `execute_trade_proposal`
   before mutating them, in a fixed order (`order_by("id")`) so two
   concurrent executions can never deadlock against each other.

## Cycle detection & persistence

`build_trade_graph()` builds an adjacency list of all `AVAILABLE`-item
wants. `find_cycles_for_user()` runs a DFS from a single user, capped at
`MAX_CYCLE_LENGTH`, returning cycles of length ≥ 3 (a 2-party mutual want
is a direct trade, surfaced separately via `DirectTradeView`, not a
"cycle").

`persist_trade_cycles()` avoids creating duplicate rows on repeated
detection calls: before inserting a new `TradeCycle`, it builds a
signature key (`build_cycle_key`, a sorted tuple of `(giver, receiver,
item)` ids) for every currently *active* persisted cycle and reuses a
match instead of inserting a duplicate. This is why `GET
/api/trades/cycles/` is safe to poll repeatedly — it doesn't accumulate
rows for the same underlying trade relationship.

## Why no `utils/` package

The brief allowed for a `utils/` module, but nothing in this codebase
needed one badly enough to justify it — every helper found a natural
home next to the thing it serves (`is_expired()` on the model,
`build_cycle_key()` in `cycle_services.py`, `_get_proposal_or_404` /
`_is_participant` as module-private helpers in `proposal_views.py`).
Adding an empty `utils/` package would have been speculative structure
with no current occupant.
