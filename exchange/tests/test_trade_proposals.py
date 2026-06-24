from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
    TradeProposal,
    TradeParticipant,
    TradeItem,
)
from exchange.services import release_reserved_items


class TradeProposalApiTests(TestCase):

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

    def test_create_trade_proposal(self):

        response = self.create_proposal()

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            TradeProposal.objects.count(),
            1,
        )

        self.assertEqual(
            TradeParticipant.objects.count(),
            3,
        )

        self.assertEqual(
            TradeItem.objects.count(),
            3,
        )

    def test_creator_must_be_participant(self):

        response = self.client.post(
            "/api/trade-proposals/",
            {
                "participants": [
                    self.user2.id,
                    self.user3.id,
                ],
                "trades": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_participant_can_accept_trade(self):

        response = self.create_proposal()

        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        response = self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/accept/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        participant = TradeParticipant.objects.get(
            proposal=proposal,
            user=self.user1,
        )

        self.assertTrue(
            participant.accepted
        )

        self.assertIsNotNone(
            participant.accepted_at
        )

    def test_non_participant_cannot_accept(self):

        response = self.create_proposal()

        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        self.client.force_authenticate(
            user=self.user4
        )

        response = self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/accept/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_trade_executes_after_all_accept(self):

        response = self.create_proposal()

        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        self.client.force_authenticate(
            user=self.user1
        )
        self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/accept/"
        )

        proposal.refresh_from_db()

        self.assertEqual(
            proposal.status,
            TradeProposal.Status.PENDING,
        )

        self.client.force_authenticate(
            user=self.user2
        )
        self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/accept/"
        )

        proposal.refresh_from_db()

        self.assertEqual(
            proposal.status,
            TradeProposal.Status.PENDING,
        )

        self.client.force_authenticate(
            user=self.user3
        )
        self.client.post(
            f"/api/trade-proposals/{proposal.public_id}/accept/"
        )

        proposal.refresh_from_db()

        self.assertEqual(
            proposal.status,
            TradeProposal.Status.EXECUTED,
        )

    def test_item_ownership_transfers(self):

        response = self.create_proposal()

        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        for user in [
            self.user1,
            self.user2,
            self.user3,
        ]:
            self.client.force_authenticate(
                user=user
            )

            self.client.post(
                f"/api/trade-proposals/{proposal.public_id}/accept/"
            )

        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.item3.refresh_from_db()

        self.assertEqual(
            self.item1.owner,
            self.user2,
        )

        self.assertEqual(
            self.item2.owner,
            self.user3,
        )

        self.assertEqual(
            self.item3.owner,
            self.user1,
        )

    def test_deleted_item_cannot_be_proposed(self):
        self.item1.is_deleted = True
        self.item1.save(update_fields=["is_deleted"])

        response = self.create_proposal()

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            TradeProposal.objects.count(),
            0,
        )

    def test_giver_must_be_participant(self):

        response = self.client.post(
            "/api/trade-proposals/",
            {
                "participants": [
                    self.user1.id,
                    self.user2.id,
                ],
                "trades": [
                    {
                        "giver": self.user3.id,
                        "receiver": self.user2.id,
                        "item": self.item3.id,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            TradeProposal.objects.count(),
            0,
        )

    def test_item_already_reserved_cannot_be_proposed_again(self):

        self.create_proposal()

        response = self.client.post(
            "/api/trade-proposals/",
            {
                "participants": [
                    self.user1.id,
                    self.user2.id,
                ],
                "trades": [
                    {
                        "giver": self.user1.id,
                        "receiver": self.user2.id,
                        "item": self.item1.id,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            TradeProposal.objects.count(),
            1,
        )

    def test_release_reserved_items_returns_item_to_available(self):

        response = self.create_proposal()

        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        proposal.status = TradeProposal.Status.REJECTED
        proposal.save(update_fields=["status"])

        release_reserved_items(proposal)

        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.item3.refresh_from_db()

        self.assertEqual(
            self.item1.status,
            Item.Status.AVAILABLE,
        )

        self.assertEqual(
            self.item2.status,
            Item.Status.AVAILABLE,
        )

        self.assertEqual(
            self.item3.status,
            Item.Status.AVAILABLE,
        )

    def test_release_reserved_items_does_not_touch_traded_items(self):

        response = self.create_proposal()

        proposal = TradeProposal.objects.get(
            public_id=response.data["public_id"]
        )

        for user in [self.user1, self.user2, self.user3]:
            self.client.force_authenticate(user=user)
            self.client.post(
                f"/api/trade-proposals/{proposal.public_id}/accept/"
            )

        release_reserved_items(proposal)

        self.item1.refresh_from_db()

        self.assertEqual(
            self.item1.status,
            Item.Status.TRADED,
        )
