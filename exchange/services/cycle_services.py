from ..models import Item, Want
from ..constants import MAX_CYCLE_LENGTH


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
            item__status=Item.Status.AVAILABLE
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
        if len(path_edges) >= max_depth:
            return

        for edge in graph.get(current_node, []):

            next_user_id = edge["target"].id

            # Cycle found
            if (
                next_user_id == start_node
                and len(path_edges) >= 2
            ):
                cycle_edges = path_edges + [edge]

                cycle_key = build_cycle_key(
                    cycle_edges
                )

                if cycle_key not in seen_cycles:
                    seen_cycles.add(cycle_key)

                    cycles.append(
                        build_cycle_response(
                            cycle_edges
                        )
                    )

                continue

            # Skip repeated participants
            if next_user_id in visited_users:
                continue

            dfs(
                start_node=start_node,
                current_node=next_user_id,
                path_edges=path_edges + [edge],
                visited_users=visited_users | {
                    next_user_id
                },
            )

    dfs(
        start_node=user_id,
        current_node=user_id,
        path_edges=[],
        visited_users={user_id},
    )

    return cycles