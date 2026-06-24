from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
    TradeProposal,
)


class TradeProposalLifecycleTests(TestCase):

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

        self.user4 = User.objects.create_user(
            username="vidhya",
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

    def create_proposal(self):
        return self.client.post(
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

    def test_participant_can_reject_pending_proposal(self):
        response = self.create_proposal()
        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        response = self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/reject/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            TradeProposal.Status.REJECTED,
        )

        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.item3.refresh_from_db()

        self.assertEqual(self.item1.status, Item.Status.AVAILABLE)
        self.assertEqual(self.item2.status, Item.Status.AVAILABLE)
        self.assertEqual(self.item3.status, Item.Status.AVAILABLE)

    def test_non_participant_cannot_reject(self):
        response = self.create_proposal()
        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        self.client.force_authenticate(user=self.user4)

        response = self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/reject/"
        )

        self.assertEqual(response.status_code, 403)
