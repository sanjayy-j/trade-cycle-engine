from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
    TradeProposal,
    TradeExecution,
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

        return response

    def accept_proposal(self, proposal):
        for user in [self.user1, self.user2, self.user3]:
            self.client.force_authenticate(user=user)
            self.client.post(
                f"/api/trade-proposals/{proposal.public_id}/accept/"
            )
        proposal.refresh_from_db()
        return proposal

    def test_execution_record_created(self):
        response = self.create_proposal()
        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        self.accept_proposal(proposal)

        self.assertEqual(
            TradeExecution.objects.count(),
            1,
        )

        self.assertEqual(
            proposal.execution.proposal,
            proposal,
        )

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

    def test_non_participant_cannot_view_history(self):
        response = self.create_proposal()
        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        self.accept_proposal(proposal)

        self.client.force_authenticate(user=self.user4)
        response = self.client.get(
            "/api/trade-history/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_history_ordering(self):
        response1 = self.create_proposal()
        proposal1 = TradeProposal.objects.get(
            public_id=response1.data["public_id"]
        )
        self.accept_proposal(proposal1)

        response2 = self.create_proposal()
        proposal2 = TradeProposal.objects.get(
            public_id=response2.data["public_id"]
        )
        self.accept_proposal(proposal2)

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
            2,
        )

        self.assertEqual(
            response.data[0]["proposal_public_id"],
            str(proposal2.public_id),
        )
        self.assertEqual(
            response.data[1]["proposal_public_id"],
            str(proposal1.public_id),
        )

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/trade-history/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )
