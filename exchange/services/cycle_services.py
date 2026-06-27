"""Trade cycle discovery and persistence: graph building, DFS search, and storage."""

from django.db import transaction

from ..constants import MAX_CYCLE_LENGTH
from ..models import Item, TradeCycle, TradeCycleParticipant, TradeCycleTrade, Want


def build_trade_graph():
    """
    Builds an adjacency list where each edge represents:
    `
    source_user -> owner_of_desired_item
    `
    along with the item that creates the relationship.
    """
    adjacency_list = {}

    wants = (
        Want.objects
        .select_related(
            "user",
            "item",
            "item__owner",
        )
        .filter(
            item__status=Item.Status.AVAILABLE,
            item__is_deleted=False,
        )
    )

    for want in wants:
        source_user = want.user
        target_user = want.item.owner

        # Defensive protection against self-loops
        if source_user == target_user:
            continue

        edge = {
            "source": source_user,
            "target": target_user,
            "item": want.item,
        }

        adjacency_list.setdefault(
            source_user.id,
            []
        ).append(edge)

    return adjacency_list


def build_cycle_key(cycle_edges):
    """
    Generates a unique key for a cycle based on the actual trades involved.

    This prevents different trade cycles with the same participants from being collapsed together.
    """
    return tuple(
        sorted(
            (
                edge["source"].id,
                edge["target"].id,
                edge["item"].id,
            )
            for edge in cycle_edges
        )
    )


def build_cycle_response(cycle_edges):
    """
    Converts a list of edges into the API-friendly cycle structure.
    """
    participants = []
    seen_participants = set()

    for edge in cycle_edges:
        user = edge["source"]

        if user.id not in seen_participants:
            seen_participants.add(user.id)
            participants.append(user)

    return {
        "cycle_length": len(participants),
        "participants": participants,
        "trades": [
            {
                "giver": edge["target"],
                "receiver": edge["source"],
                "item": edge["item"],
            }
            for edge in cycle_edges
        ],
    }


def find_cycles_for_user(
    graph,
    user_id,
    max_depth=MAX_CYCLE_LENGTH,
):
    """
    Finds trade cycles involving a specific user.

    Supports:
        3-way cycles
        4-way cycles
        5-way cycles
        ...
        max_depth-way cycles
    """

    cycles = []
    seen_cycles = set()

    def dfs(
        start_node,
        current_node,
        path_edges,
        visited_users,
    ):
        """Depth-first walk that records a cycle whenever it returns to start_node."""
        if len(path_edges) >= max_depth:
            return

        for edge in graph.get(current_node, []):

            next_user_id = edge["target"].id

            # Cycle found
            if next_user_id == start_node and len(path_edges) >= 2:
                cycle_edges = path_edges + [edge]
                cycle_key = build_cycle_key(cycle_edges)

                if cycle_key not in seen_cycles:
                    seen_cycles.add(cycle_key)
                    cycles.append(build_cycle_response(cycle_edges))

                continue

            # Skip repeated participants
            if next_user_id in visited_users:
                continue

            dfs(
                start_node=start_node,
                current_node=next_user_id,
                path_edges=path_edges + [edge],
                visited_users=visited_users | {next_user_id},
            )

    dfs(
        start_node=user_id,
        current_node=user_id,
        path_edges=[],
        visited_users={user_id},
    )

    return cycles


def _active_cycles_by_key():
    """
    Maps each active ``TradeCycle``'s trade signature (via
    ``build_cycle_key``) to the cycle itself.

    Used by ``persist_trade_cycles`` to detect when a freshly detected
    cycle is identical to one already persisted and active, so it can be
    reused instead of creating a duplicate row.
    """
    cycles_by_id = {
        cycle.id: cycle
        for cycle in TradeCycle.objects.filter(active=True)
    }

    edges_by_cycle_id = {}

    trades = (
        TradeCycleTrade.objects
        .filter(cycle__active=True)
        .select_related("giver", "receiver", "item")
    )

    for trade in trades:
        edges_by_cycle_id.setdefault(trade.cycle_id, []).append(
            {
                "source": trade.receiver,
                "target": trade.giver,
                "item": trade.item,
            }
        )

    keys = {}

    for cycle_id, edges in edges_by_cycle_id.items():
        keys[build_cycle_key(edges)] = cycles_by_id[cycle_id]

    return keys


@transaction.atomic
def persist_trade_cycles(
    cycle_responses,
):
    """
    Persists detected trade cycles and their
    associated participants/trades.

    Behavior:
        Before creating a new ``TradeCycle``, checks whether an active
        cycle with an identical trade signature (same giver/receiver/item
        triples) already exists, and reuses it instead of persisting a
        duplicate. This keeps repeated calls to the cycle-detection
        endpoint from accumulating duplicate rows for the same underlying
        relationship.

    All writes occur within a single database
    transaction to prevent partially-created
    cycles from being stored.
    """

    existing_keys = _active_cycles_by_key()

    created_cycles = []

    for cycle_response in cycle_responses:

        signature_edges = [
            {
                "source": trade["receiver"],
                "target": trade["giver"],
                "item": trade["item"],
            }
            for trade in cycle_response["trades"]
        ]

        cycle_key = build_cycle_key(signature_edges)

        if cycle_key in existing_keys:
            created_cycles.append(existing_keys[cycle_key])
            continue

        cycle = TradeCycle.objects.create()

        participants = [
            TradeCycleParticipant(
                cycle=cycle,
                user=user,
            )
            for user in cycle_response["participants"]
        ]

        TradeCycleParticipant.objects.bulk_create(participants)

        trades = [
            TradeCycleTrade(
                cycle=cycle,
                giver=trade["giver"],
                receiver=trade["receiver"],
                item=trade["item"],
            )
            for trade in cycle_response["trades"]
        ]

        TradeCycleTrade.objects.bulk_create(trades)

        existing_keys[cycle_key] = cycle
        created_cycles.append(cycle)

    return created_cycles
