from .models import Want


def build_trade_graph():
    graph = {}

    wants = Want.objects.select_related(
        "user",
        "item",
        "item__owner",
    )

    for want in wants:
        source_user = want.user
        target_user = want.item.owner

        if source_user == target_user:
            continue

        edge = {
            "source": source_user,
            "target": target_user,
            "item": want.item,
        }

        graph.setdefault(
            source_user.id,
            []
        ).append(edge)

    return graph


def find_three_cycles(graph):
    cycles = []
    seen = set()

    for a_id in graph:

        for edge_ab in graph.get(a_id, []):
            b_id = edge_ab["target"].id

            for edge_bc in graph.get(b_id, []):
                c_id = edge_bc["target"].id

                if c_id == a_id:
                    continue

                for edge_ca in graph.get(c_id, []):

                    if edge_ca["target"].id != a_id:
                        continue

                    cycle_key = tuple(
                        sorted(
                            [a_id, b_id, c_id]
                        )
                    )

                    if cycle_key in seen:
                        continue

                    seen.add(cycle_key)

                    cycles.append({
                        "participants": [
                            edge_ab["source"],
                            edge_ab["target"],
                            edge_bc["target"],
                        ],
                        "trades": [
                            {
                                "giver": edge_ab["target"],
                                "receiver": edge_ab["source"],
                                "item": edge_ab["item"],
                            },
                            {
                                "giver": edge_bc["target"],
                                "receiver": edge_bc["source"],
                                "item": edge_bc["item"],
                            },
                            {
                                "giver": edge_ca["target"],
                                "receiver": edge_ca["source"],
                                "item": edge_ca["item"],
                            },
                        ]
                    })

    return cycles