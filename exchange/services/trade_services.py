from django.db import transaction
from django.utils import timezone

from ..models import (
    TradeProposal,
    TradeParticipant,
    TradeItem,
    TradeExecution,
    Item,
)

def create_trade_proposal(
    participants,
    trades,
):
    with transaction.atomic():

        proposal = TradeProposal.objects.create()

        TradeParticipant.objects.bulk_create(
            [
                TradeParticipant(
                    proposal=proposal,
                    user=user,
                )
                for user in participants
            ]
        )

        TradeItem.objects.bulk_create(
            [
                TradeItem(
                    proposal=proposal,
                    giver=trade["giver"],
                    receiver=trade["receiver"],
                    item=trade["item"],
                )
                for trade in trades
            ]
        )

    return proposal

def accept_trade_proposal(
    proposal,
    user,
):
    with transaction.atomic():
        participant = proposal.participants.select_for_update().get(
            user=user
        )

        participant.accepted = True
        participant.accepted_at = timezone.now()
        participant.save(update_fields=["accepted", "accepted_at"])

        all_accepted = not proposal.participants.filter(
            accepted=False
        ).exists()

        if all_accepted:
            execute_trade_proposal(proposal)

    return proposal

def execute_trade_proposal(
    proposal,
):
    with transaction.atomic():
        trade_items = (
            proposal.trade_items
            .select_related("item", "receiver")
            .all()
        )

        for trade_item in trade_items:
            item = trade_item.item
            item.owner = trade_item.receiver
            item.status = Item.Status.TRADED
            item.save(
                update_fields=[
                    "owner",
                    "status",
                    "updated_at",
                ]
            )

        proposal.status = TradeProposal.Status.EXECUTED
        proposal.save(update_fields=["status", "updated_at"])

        TradeExecution.objects.get_or_create(
            proposal=proposal,
        )