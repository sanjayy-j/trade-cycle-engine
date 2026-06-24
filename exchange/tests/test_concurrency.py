import threading

from django.db import connection
from django.test import TransactionTestCase

from exchange.models import User, Item
from exchange.services import create_trade_proposal, ItemNotAvailableError


class TradeProposalConcurrencyTests(TransactionTestCase):
    """
    Exercises the select_for_update reservation lock in
    create_trade_proposal under real concurrent access.

    Uses TransactionTestCase (not TestCase) so each thread gets its own
    database connection and transaction, allowing the row lock taken by
    one thread to actually block the other rather than both operating
    inside the same wrapped test transaction.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="alice",
            password="test123",
        )
        self.user2 = User.objects.create_user(
            username="bob",
            password="test123",
        )
        self.item = Item.objects.create(
            name="Contested Item",
            owner=self.user1,
        )

    def test_only_one_concurrent_proposal_can_reserve_the_same_item(self):
        outcomes = []

        def attempt_create():
            try:
                create_trade_proposal(
                    [self.user1, self.user2],
                    [
                        {
                            "giver": self.user1,
                            "receiver": self.user2,
                            "item": self.item,
                        }
                    ],
                )
                outcomes.append("created")
            except ItemNotAvailableError:
                outcomes.append("rejected")
            finally:
                connection.close()

        threads = [
            threading.Thread(target=attempt_create)
            for _ in range(2)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(outcomes.count("created"), 1)
        self.assertEqual(outcomes.count("rejected"), 1)

        self.item.refresh_from_db()

        self.assertEqual(
            self.item.status,
            Item.Status.RESERVED,
        )
