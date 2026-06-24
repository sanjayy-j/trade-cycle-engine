from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
    TradeProposal,
)


class TradeHistoryApiTests(TestCase):

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

        self.client.force_authenticate(
            user=self.user1
        )

    def create_proposal(self, items=None):
        item1, item2, item3 = items or (
            self.item1,
            self.item2,
            self.item3,
        )

        response = self.client.post(
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
                        "item": item1.id,
                    },
                    {
                        "giver": self.user2.id,
                        "receiver": self.user3.id,
                        "item": item2.id,
                    },
                    {
                        "giver": self.user3.id,
                        "receiver": self.user1.id,
                        "item": item3.id,
                    },
                ],
            },
            format="json",
        )

        return response

    def accept_proposal(self, proposal):
        for user in [self.user1, self.user2, self.user3]:
            self.client.force_authenticate(user=user)
            self.client.post(
                f"/api/trade-proposals/{proposal.public_id}/accept/"
            )
        proposal.refresh_from_db()
        return proposal

    def test_user_can_view_trade_history(self):
        response = self.create_proposal()
        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        self.accept_proposal(proposal)

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(
            "/api/trade-history/"
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
            response.data[0]["proposal_public_id"],
            str(proposal.public_id),
        )
