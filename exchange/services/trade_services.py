"""Trade proposal lifecycle: creation, acceptance, rejection, expiry, and execution."""

import logging

from django.db import transaction
from django.utils import timezone

from ..exceptions import ItemNotAvailableError, ProposalNotPendingError
from ..models import (
    TradeProposal,
    TradeParticipant,
    TradeItem,
    TradeExecution,
    Item,
)

logger = logging.getLogger("exchange")


def create_trade_proposal(
    participants,
    trades,
):
    """
    Creates a pending trade proposal with its participants and trade items.

    Behavior:
        Locks every referenced item with ``select_for_update`` and verifies
        it is still ``AVAILABLE`` before creating the proposal, then marks
        all of them ``RESERVED``. This closes the race window where two
        concurrent proposals could both claim the same item.

    Side effects:
        Creates one ``TradeProposal`` row, one ``TradeParticipant`` row per
        participant (all defaulting to unaccepted), one ``TradeItem`` row
        per trade, and flips every referenced item to ``RESERVED``.

    Transaction behavior:
        Item locking, availability checks, and all inserts happen within a
        single atomic block; if any item is unavailable or any insert
        fails, nothing is persisted.

    Returns:
        The newly created ``TradeProposal`` instance.

    Raises:
        ItemNotAvailableError: if any referenced item is not ``AVAILABLE``.
    """
    item_ids = {trade["item"].id for trade in trades}

    with transaction.atomic():
        locked_items = list(
            Item.objects.select_for_update()
            .filter(id__in=item_ids)
            .order_by("id")
        )

        unavailable = [
            item for item in locked_items
            if item.status != Item.Status.AVAILABLE
        ]

        if unavailable:
            logger.warning(
                "Trade proposal rejected: items not available: %s",
                [item.id for item in unavailable],
            )
            raise ItemNotAvailableError(
                "The following items are no longer available: "
                + ", ".join(item.name for item in unavailable)
            )

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

        Item.objects.filter(id__in=item_ids).update(
            status=Item.Status.RESERVED,
        )

    logger.info(
        "Trade proposal %s created with %d participant(s), %d item(s)",
        proposal.public_id,
        len(participants),
        len(item_ids),
    )

    return proposal


def release_reserved_items(proposal):
    """
    Releases items reserved by a proposal back to AVAILABLE.

    Behavior:
        Intended for use when a proposal is rejected or expires without
        executing. Reverts every item on the proposal's ``TradeItem`` rows
        that is still ``RESERVED`` back to ``AVAILABLE``, freeing it for
        new proposals. Items already ``TRADED`` (e.g. from an unrelated
        completed proposal) are left untouched.

    Side effects:
        Mutates ``Item.status`` for the proposal's reserved items.

    Transaction behavior:
        Item lookups and updates happen within a single atomic block.

    Returns:
        None.
    """
    with transaction.atomic():
        item_ids = proposal.trade_items.values_list("item_id", flat=True)

        Item.objects.select_for_update().filter(
            id__in=list(item_ids),
            status=Item.Status.RESERVED,
        ).update(status=Item.Status.AVAILABLE)

    logger.info(
        "Released reserved items for trade proposal %s",
        proposal.public_id,
    )


def expire_trade_proposal_if_needed(proposal):
    """
    Expires a proposal if it is still PENDING past its expiry.

    Behavior:
        Locks the proposal row and re-checks its status/expiry under the
        lock (in case another request already transitioned it). If it is
        eligible, flips its status to ``EXPIRED`` and releases its
        reserved items via ``release_reserved_items``.

    Side effects:
        May mutate ``TradeProposal.status`` and the status of its reserved
        items. Mutates the passed-in ``proposal`` instance's ``status``
        in place when expiry occurs, so callers see the updated value
        without an extra ``refresh_from_db``.

    Transaction behavior:
        The proposal row is locked with ``select_for_update``; the status
        change and item release happen atomically.

    Returns:
        bool: True if the proposal was just expired, False otherwise.
    """
    with transaction.atomic():
        locked = TradeProposal.objects.select_for_update().get(
            pk=proposal.pk,
        )

        if not locked.is_expired():
            return False

        locked.status = TradeProposal.Status.EXPIRED
        locked.save(update_fields=["status", "updated_at"])

        release_reserved_items(locked)

    proposal.status = TradeProposal.Status.EXPIRED

    logger.info(
        "Trade proposal %s expired",
        proposal.public_id,
    )

    return True


def _raise_if_just_expired(proposal, action):
    """Expires the proposal if it's due, then raises if that just happened."""
    if expire_trade_proposal_if_needed(proposal):
        raise ProposalNotPendingError(
            f"This trade proposal has expired and can no longer be {action}."
        )


def reject_trade_proposal(proposal, user):
    """
    Rejects a pending trade proposal and releases its reserved items.

    Behavior:
        A single participant declining is enough to cancel the whole
        multi-party proposal. First lazily expires the proposal if it is
        past its expiry (in which case rejection no longer applies), then
        requires the proposal to be ``PENDING``.

    Side effects:
        Mutates ``TradeProposal.status`` to ``REJECTED`` and releases the
        proposal's reserved items back to ``AVAILABLE``.

    Transaction behavior:
        The proposal row is locked with ``select_for_update``; the status
        change and item release happen atomically.

    Returns:
        The same ``TradeProposal`` instance, with ``status`` updated.

    Raises:
        ProposalNotPendingError: if the proposal is not (or no longer)
        ``PENDING``.
    """
    _raise_if_just_expired(proposal, "rejected")

    with transaction.atomic():
        locked = TradeProposal.objects.select_for_update().get(
            pk=proposal.pk,
        )

        if locked.status != TradeProposal.Status.PENDING:
            raise ProposalNotPendingError(
                f"This trade proposal is {locked.status} and cannot be "
                "rejected."
            )

        locked.status = TradeProposal.Status.REJECTED
        locked.save(update_fields=["status", "updated_at"])

        release_reserved_items(locked)

    proposal.status = TradeProposal.Status.REJECTED

    logger.info(
        "Trade proposal %s rejected by user %s",
        proposal.public_id,
        user.id,
    )

    return proposal


def accept_trade_proposal(
    proposal,
    user,
):
    """
    Records a participant's acceptance of a trade proposal.

    Behavior:
        Lazily expires the proposal first if it is past its expiry, then
        requires it to be ``PENDING``. Marks the calling user's
        ``TradeParticipant`` row as accepted. If every participant has now
        accepted, the proposal is executed immediately as part of the
        same transaction.

    Side effects:
        Updates the participant's ``accepted``/``accepted_at`` fields and,
        when unanimous, triggers ``execute_trade_proposal`` (item ownership
        transfers, proposal status change, execution record creation).

    Transaction behavior:
        The participant row is locked with ``select_for_update`` and the
        acceptance check plus any resulting execution run atomically,
        preventing a race where two simultaneous acceptances both observe
        an incomplete acceptance set.

    Returns:
        The same ``TradeProposal`` instance (not refreshed from DB).

    Raises:
        ProposalNotPendingError: if the proposal is not (or no longer)
        ``PENDING``.
    """
    _raise_if_just_expired(proposal, "accepted")

    if proposal.status != TradeProposal.Status.PENDING:
        raise ProposalNotPendingError(
            f"This trade proposal is {proposal.status} and can no longer "
            "be accepted."
        )

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
    """
    Executes a fully-accepted trade proposal by transferring item ownership.

    Behavior:
        Locks every referenced ``Item`` row with ``select_for_update``
        (ordered by id to avoid lock-ordering deadlocks) before mutating
        it, then reassigns each item's owner to the trade's receiver and
        marks it ``TRADED``.

    Side effects:
        Mutates ``Item.owner``/``Item.status`` for every traded item, sets
        the proposal status to ``EXECUTED``, and creates (or fetches) a
        ``TradeExecution`` record for the proposal.

    Transaction behavior:
        Item locking, all item updates, the proposal status change, and
        the execution record creation happen atomically.

    Returns:
        None.
    """
    with transaction.atomic():
        trade_items = list(
            proposal.trade_items
            .select_related("receiver")
            .order_by("item_id")
        )

        item_ids = [trade_item.item_id for trade_item in trade_items]

        locked_items = {
            item.id: item
            for item in Item.objects.select_for_update()
            .filter(id__in=item_ids)
            .order_by("id")
        }

        for trade_item in trade_items:
            item = locked_items[trade_item.item_id]
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

    logger.info("Trade proposal %s executed", proposal.public_id)
