"""Management command that seeds a realistic, idempotent demo dataset."""

from django.core.management.base import BaseCommand

from ...constants import MAX_CYCLE_LENGTH
from ...models import Item, User, Want
from ...services import (
    ItemNotAvailableError,
    build_trade_graph,
    create_trade_proposal,
    find_cycles_for_user,
)

# Demo-only credential, intentionally not a secret - reviewers need it to
# log in. Lives only here; never reused elsewhere in the codebase.
DEMO_PASSWORD = "Demo@123"

# (username, email)
DEMO_USERS = [
    ("alice", "alice@example.com"),
    ("bob", "bob@example.com"),
    ("charlie", "charlie@example.com"),
    ("david", "david@example.com"),
    ("emma", "emma@example.com"),
    ("frank", "frank@example.com"),
    ("grace", "grace@example.com"),
    ("henry", "henry@example.com"),
]

# (item name, description, category, owner username). Category has no
# dedicated model field, so it's folded into the description text.
DEMO_ITEMS = [
    ("Laptop", "14-inch ultrabook, 16GB RAM", "Electronics", "alice"),
    ("DSLR Camera", "Entry-level DSLR, 18-55mm lens", "Electronics", "bob"),
    ("Football", "Size 5 match football", "Sports", "charlie"),
    ("Mechanical Keyboard", "Hot-swappable, tactile", "Electronics", "david"),
    ("Smart Watch", "Fitness tracking, heart-rate", "Electronics", "emma"),
    ("Bicycle", "Hybrid bike, lightly used", "Sports", "frank"),
    ("Chess Set", "Wooden tournament-size chess set", "Games", "grace"),
    ("Monitor", "27-inch 1440p display", "Electronics", "henry"),
    ("Backpack", "40L hiking backpack", "Accessories", "alice"),
    ("Headphones", "Noise-cancelling over-ear", "Electronics", "bob"),
    ("Tablet", "10-inch tablet, 64GB storage", "Electronics", "charlie"),
    ("Guitar", "Acoustic guitar, steel strings", "Music", "david"),
    ("Sunglasses", "Polarized aviator sunglasses", "Accessories", "emma"),
    ("Skateboard", "Maple deck, street setup", "Sports", "frank"),
    ("Board Game Set", "Set of 5 classic board games", "Games", "grace"),
    ("Desk Lamp", "LED desk lamp, adjustable arm", "Home", "henry"),
    ("Coffee Maker", "Drip coffee maker, 12-cup", "Home", "alice"),
    ("Running Shoes", "Road running shoes, size 9", "Sports", "bob"),
]

# (wanting user, wanted item name). Structured so the resulting want graph
# is guaranteed to contain:
#   - a direct trade: alice <-> bob (each wants the other's item)
#   - a 3-way cycle: charlie -> david -> emma -> charlie
# Everything else is ordinary, one-directional interest; any further
# matches/cycles that incidentally fall out of them are harmless bonus
# demo data, not a correctness requirement.
DEMO_WANTS = [
    ("alice", "DSLR Camera"),
    ("bob", "Laptop"),
    ("charlie", "Mechanical Keyboard"),
    ("david", "Smart Watch"),
    ("emma", "Football"),
    ("alice", "Tablet"),
    ("alice", "Sunglasses"),
    ("bob", "Chess Set"),
    ("bob", "Desk Lamp"),
    ("charlie", "Bicycle"),
    ("charlie", "Board Game Set"),
    ("david", "Backpack"),
    ("david", "Headphones"),
    ("emma", "Skateboard"),
    ("emma", "Monitor"),
    ("frank", "Guitar"),
    ("frank", "Coffee Maker"),
    ("grace", "Running Shoes"),
    ("grace", "Laptop"),
    ("henry", "Football"),
    ("henry", "Smart Watch"),
]

# The proposal demonstration reuses the alice <-> bob direct trade so the
# 3-way cycle's items stay AVAILABLE for the cycle-detection demo.
DEMO_PROPOSAL_PARTICIPANTS = ("alice", "bob")
DEMO_PROPOSAL_TRADES = (
    ("bob", "alice", "DSLR Camera"),
    ("alice", "bob", "Laptop"),
)


class Command(BaseCommand):
    """Seed the database with demo users, items, wants, and a proposal."""

    help = "Seed a realistic, idempotent demo dataset for manual exploration."

    def handle(self, *args, **options):
        users = self._seed_users()
        items = self._seed_items(users)
        self._seed_wants(users, items)
        self._seed_demo_proposal(users, items)
        self._verify(users)

        self.stdout.write(
            self.style.SUCCESS("\nDemo data successfully generated.")
        )
        self.stdout.write(
            f"Log in as any of {', '.join(users)} with password "
            f"'{DEMO_PASSWORD}'."
        )

    def _seed_users(self):
        self.stdout.write("Creating demo users...")
        users = {}
        new_count = 0

        for username, email in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "role": User.Role.USER},
            )

            if created:
                # get_or_create's defaults= would store the password in
                # plaintext, so it's set (and hashed) separately.
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
                new_count += 1

            users[username] = user

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] {len(users)} users ready ({new_count} new)"
            )
        )
        return users

    def _seed_items(self, users):
        self.stdout.write("\nCreating demo items...")
        items = {}
        new_count = 0

        for name, description, category, owner_username in DEMO_ITEMS:
            item, created = Item.objects.get_or_create(
                name=name,
                owner=users[owner_username],
                defaults={"description": f"{description} ({category})"},
            )

            if created:
                new_count += 1

            items[name] = item

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] {len(items)} items ready ({new_count} new)"
            )
        )
        return items

    def _seed_wants(self, users, items):
        self.stdout.write("\nCreating wants...")
        new_count = 0

        for username, item_name in DEMO_WANTS:
            _, created = Want.objects.get_or_create(
                user=users[username],
                item=items[item_name],
            )

            if created:
                new_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] {len(DEMO_WANTS)} wants ready ({new_count} new)"
            )
        )

    def _seed_demo_proposal(self, users, items):
        """
        Create one pending trade proposal via the real service function.

        Skips cleanly (no error) if the demo items are no longer
        AVAILABLE - either because this command already ran and reserved
        them, or because a reviewer has since acted on them through the
        API.
        """
        self.stdout.write("\nCreating demo trade proposal...")

        participants = [users[name] for name in DEMO_PROPOSAL_PARTICIPANTS]
        trades = [
            {
                "giver": users[giver],
                "receiver": users[receiver],
                "item": items[item_name],
            }
            for giver, receiver, item_name in DEMO_PROPOSAL_TRADES
        ]

        try:
            create_trade_proposal(participants, trades)
        except ItemNotAvailableError:
            self.stdout.write(
                self.style.SUCCESS("[OK] Demo trade proposal already exists")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                "[OK] 1 pending trade proposal ready "
                f"({' <-> '.join(DEMO_PROPOSAL_PARTICIPANTS)})"
            )
        )

    def _verify(self, users):
        self.stdout.write("\nVerifying generated data...")

        if self._has_direct_trade():
            self.stdout.write(
                self.style.SUCCESS("[OK] Direct trade available")
            )
        else:
            self.stdout.write(
                self.style.WARNING("[MISSING] No direct trade found")
            )

        if self._has_cycle(users):
            self.stdout.write(
                self.style.SUCCESS("[OK] 3-way trade cycle available")
            )
        else:
            self.stdout.write(
                self.style.WARNING("[MISSING] No trade cycle found")
            )

    @staticmethod
    def _has_direct_trade():
        """Mirrors DirectTradeView's mutual-want check, for verification."""
        for want in Want.objects.select_related("user", "item__owner"):
            if Want.objects.filter(
                user=want.item.owner,
                item__owner=want.user,
            ).exists():
                return True
        return False

    @staticmethod
    def _has_cycle(users):
        """Mirrors TradeCycleView's detection logic, for verification."""
        graph = build_trade_graph()
        return any(
            find_cycles_for_user(graph, user.id, max_depth=MAX_CYCLE_LENGTH)
            for user in users.values()
        )
