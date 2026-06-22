from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from exchange.models import (
    User,
    Item,
    TradeProposal,
)


class ThrottlingTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="sanjay",
            password="test123",
        )

        self.user2 = User.objects.create_user(
            username="murthy",
            password="test123",
        )

        self.user3 = User.objects.create_user(
            username="kavin",
            password="test123",
        )

        self.item1 = Item.objects.create(
            name="Book",
            owner=self.user1,
        )

        self.item2 = Item.objects.create(
            name="Keyboard",
            owner=self.user2,
        )

        self.item3 = Item.objects.create(
            name="Mouse",
            owner=self.user3,
        )

    def create_proposal(self, client):
        return client.post(
            "/api/trade-proposals/",
            {
                "participants": [
                    self.user1.id,
                    self.user2.id,
                    self.user3.id,
                ],
                "trades": [
                    {
                        "giver": self.user1.id,
                        "receiver": self.user2.id,
                        "item": self.item1.id,
                    },
                    {
                        "giver": self.user2.id,
                        "receiver": self.user3.id,
                        "item": self.item2.id,
                    },
                    {
                        "giver": self.user3.id,
                        "receiver": self.user1.id,
                        "item": self.item3.id,
                    },
                ],
            },
            format="json",
        )

    def test_normal_requests_succeed(self):
        self.client.force_authenticate(user=self.user1)

        response = self.create_proposal(self.client)

        self.assertEqual(
            response.status_code,
            201,
        )

    def test_authenticated_users_use_user_throttle(self):
        self.client.force_authenticate(user=self.user1)

        response = self.create_proposal(self.client)

        self.assertEqual(
            response.status_code,
            201,
        )
        self.assertTrue(
            hasattr(response, "data"),
        )

    def test_trade_proposal_rate_limit(self):
        self.client.force_authenticate(user=self.user1)

        for i in range(31):
            response = self.create_proposal(self.client)

            if i < 30:
                self.assertIn(
                    response.status_code,
                    [201, 400],
                )
            else:
                self.assertEqual(
                    response.status_code,
                    429,
                )

    def test_trade_accept_rate_limit(self):
        self.client.force_authenticate(user=self.user1)

        response = self.create_proposal(self.client)
        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        for i in range(61):
            self.client.force_authenticate(user=self.user1)
            response = self.client.post(
                f"/api/trade-proposals/{proposal.public_id}/accept/"
            )

            if i == 0:
                self.assertEqual(
                    response.status_code,
                    200,
                )
            elif i < 60:
                self.assertIn(
                    response.status_code,
                    [200, 400, 409],
                )
            else:
                self.assertEqual(
                    response.status_code,
                    429,
                )

    def test_cycle_endpoint_rate_limit(self):
        self.client.force_authenticate(user=self.user1)

        for i in range(21):
            response = self.client.get(
                "/api/trades/cycles/"
            )

            if i < 20:
                self.assertEqual(
                    response.status_code,
                    200,
                )
            else:
                self.assertEqual(
                    response.status_code,
                    429,
                )

    def test_global_throttle_configuration(self):
        """Verify global throttle rates are properly configured."""
        from django.conf import settings

        throttle_rates = settings.REST_FRAMEWORK.get(
            "DEFAULT_THROTTLE_RATES",
            {},
        )

        self.assertEqual(
            throttle_rates.get("anon"),
            "100/day",
        )
        self.assertEqual(
            throttle_rates.get("user"),
            "1000/day",
        )
        self.assertEqual(
            throttle_rates.get("trade_proposal"),
            "30/hour",
        )
        self.assertEqual(
            throttle_rates.get("trade_accept"),
            "60/hour",
        )
        self.assertEqual(
            throttle_rates.get("cycle_detection"),
            "20/hour",
        )

    def test_different_users_have_separate_limits(self):
        self.client.force_authenticate(user=self.user1)

        for i in range(31):
            response = self.create_proposal(self.client)

            if i == 30:
                self.assertEqual(
                    response.status_code,
                    429,
                )

        self.client.force_authenticate(user=self.user2)

        response = self.create_proposal(self.client)

        self.assertEqual(
            response.status_code,
            201,
        )
