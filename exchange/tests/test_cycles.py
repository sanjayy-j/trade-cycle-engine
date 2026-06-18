from django.test import TestCase
from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
    Want,
)

from exchange.services import (
    build_trade_graph,
    find_cycles_for_user,
)

class CycleDetectionTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="sanjay",
            password="test123"
        )

        self.user2 = User.objects.create_user(
            username="murthy",
            password="test123"
        )

        self.user3 = User.objects.create_user(
            username="vidhya",
            password="test123"
        )

        self.user4 = User.objects.create_user(
            username="kavin",
            password="test123"
        )

        self.user5 = User.objects.create_user(
            username="alice",
            password="test123"
        )

        self.user6 = User.objects.create_user(
            username="bob",
            password="test123"
        )

        self.item1 = Item.objects.create(
            name="Keyboard",
            owner=self.user1,
        )

        self.item2 = Item.objects.create(
            name="Laptop",
            owner=self.user2,
        )

        self.item3 = Item.objects.create(
            name="Monitor",
            owner=self.user3,
        )

        self.item4 = Item.objects.create(
            name="Mouse",
            owner=self.user4,
        )

        self.item5 = Item.objects.create(
            name="Speaker",
            owner=self.user5,
        )

        self.item6 = Item.objects.create(
            name="Tablet",
            owner=self.user6,
        )

    def test_no_cycle_found(self):
        graph = {
            self.user1.id: [
                {
                    "source": self.user1,
                    "target": self.user2,
                    "item": self.item2,
                }
            ],

            self.user2.id: [
                {
                    "source": self.user2,
                    "target": self.user3,
                    "item": self.item3,
                }
            ],
        }

        cycles = find_cycles_for_user(
            graph,
            self.user1.id,
        )

        self.assertEqual(
            len(cycles),
            0,
        )

    def test_detects_three_way_cycle(self):
        graph = {
            self.user1.id: [
                {
                    "source": self.user1,
                    "target": self.user2,
                    "item": self.item2,
                }
            ],

            self.user2.id: [
                {
                    "source": self.user2,
                    "target": self.user3,
                    "item": self.item3,
                }
            ],

            self.user3.id: [
                {
                    "source": self.user3,
                    "target": self.user1,
                    "item": self.item1,
                }
            ],
        }

        cycles = find_cycles_for_user(
            graph,
            self.user1.id,
        )

        self.assertEqual(
            len(cycles),
            1,
        )

        self.assertEqual(
            cycles[0]["cycle_length"],
            3,
        )

    def test_detects_four_way_cycle(self):
        graph = {
            self.user1.id: [
                {
                    "source": self.user1,
                    "target": self.user2,
                    "item": self.item2,
                }
            ],

            self.user2.id: [
                {
                    "source": self.user2,
                    "target": self.user3,
                    "item": self.item3,
                }
            ],

            self.user3.id: [
                {
                    "source": self.user3,
                    "target": self.user4,
                    "item": self.item4,
                }
            ],

            self.user4.id: [
                {
                    "source": self.user4,
                    "target": self.user1,
                    "item": self.item1,
                }
            ],
        }

        cycles = find_cycles_for_user(
            graph,
            self.user1.id,
        )

        self.assertEqual(
            len(cycles),
            1,
        )

        self.assertEqual(
            cycles[0]["cycle_length"],
            4,
        )

    def test_max_depth_respected(self):
        graph = {
            self.user1.id: [
                {
                    "source": self.user1,
                    "target": self.user2,
                    "item": self.item2,
                }
            ],

            self.user2.id: [
                {
                    "source": self.user2,
                    "target": self.user3,
                    "item": self.item3,
                }
            ],

            self.user3.id: [
                {
                    "source": self.user3,
                    "target": self.user4,
                    "item": self.item4,
                }
            ],

            self.user4.id: [
                {
                    "source": self.user4,
                    "target": self.user5,
                    "item": self.item5,
                }
            ],

            self.user5.id: [
                {
                    "source": self.user5,
                    "target": self.user6,
                    "item": self.item6,
                }
            ],

            self.user6.id: [
                {
                    "source": self.user6,
                    "target": self.user1,
                    "item": self.item1,
                }
            ],
        }

        cycles = find_cycles_for_user(
            graph,
            self.user1.id,
            max_depth=5,
        )

        self.assertEqual(
            len(cycles),
            0,
        )

    def test_build_trade_graph(self):
        Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        graph = build_trade_graph()

        self.assertIn(
            self.user1.id,
            graph,
        )

        self.assertEqual(
            len(graph[self.user1.id]),
            1,
        )

        edge = graph[self.user1.id][0]

        self.assertEqual(
            edge["source"],
            self.user1,
        )

        self.assertEqual(
            edge["target"],
            self.user2,
        )

        self.assertEqual(
            edge["item"],
            self.item2,
        )

    def test_self_loop_not_added_to_graph(self):
        Want.objects.create(
            user=self.user1,
            item=self.item1,
        )

        graph = build_trade_graph()

        self.assertNotIn(
            self.user1.id,
            graph,
        )

    def test_cycles_endpoint_returns_200(self):
        Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        Want.objects.create(
            user=self.user2,
            item=self.item3,
        )

        Want.objects.create(
            user=self.user3,
            item=self.item1,
        )

        self.client.force_authenticate(
            user=self.user1
        )

        response = self.client.get(
            "/api/trades/cycles/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["cycle_length"],
            3,
        )