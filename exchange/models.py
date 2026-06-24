"""Domain models for users, items, wants, trade proposals, and trade cycles."""

import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


def _default_expiry():
    return timezone.now() + timedelta(hours=24)


def default_cycle_expiry():
    """
    Return the default expiration time for a trade cycle.

    Trade cycles remain active for 24 hours unless
    explicitly completed or deactivated.
    """

    return _default_expiry()


def default_proposal_expiry():
    """
    Return the default expiration time for a trade proposal.

    Pending proposals expire 24 hours after creation unless
    accepted, rejected, or executed before then.
    """

    return _default_expiry()


class User(AbstractUser):
    """
    Custom application user supporting role-based access control.

    Extends Django's default user model with application-specific
    roles used for authorization.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)


class Item(models.Model):
    """
    Represents a tradable item owned by a user.

    Items serve as the primary assets within the trading
    ecosystem and can participate in direct or cyclic trades.
    """

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        TRADED = "TRADED", "Traded"

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="items",
    )

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Want(models.Model):
    """
    Represents a user's interest in an item.

    A want creates a directed relationship between a user
    and the owner of the desired item, forming the trade graph.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wants",
    )

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="wanted_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "item"], name="unique_user_item_want"
            )
        ]

    def __str__(self):
        return f"{self.user.username} wants {self.item.name}"


class TradeProposal(models.Model):
    """
    Represents a proposed multi-party trade agreement.

    A proposal remains pending until all participants
    approve the trade, after which it can be executed.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        EXECUTED = "EXECUTED", "Executed"
        EXPIRED = "EXPIRED", "Expired"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    expires_at = models.DateTimeField(
        default=default_proposal_expiry,
        db_index=True,
    )

    def is_expired(self):
        """Returns True if this proposal is still PENDING past its expiry."""
        return (
            self.status == TradeProposal.Status.PENDING
            and timezone.now() >= self.expires_at
        )

    def __str__(self):
        return f"Trade Proposal " f"{self.public_id}"


class TradeExecution(models.Model):
    """
    Stores the execution record for a completed trade proposal.

    Created once a proposal has been fully accepted and
    all ownership transfers have been performed.
    """

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    proposal = models.OneToOneField(
        TradeProposal,
        on_delete=models.CASCADE,
        related_name="execution",
    )

    executed_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Trade Execution " f"{self.public_id}"


class TradeParticipant(models.Model):
    """
    Associates a user with a trade proposal.

    Tracks participant approval state during the trade
    negotiation workflow. Unlike TradeCycleParticipant,
    this model represents an active transactional entity
    that directly influences proposal acceptance and
    execution.
    """

    proposal = models.ForeignKey(
        TradeProposal,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trade_participations",
    )

    accepted = models.BooleanField(
        default=False,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proposal",
                    "user",
                ],
                name=("unique_user_per_proposal"),
            )
        ]

    def __str__(self):
        return f"{self.user.username} " f"in {self.proposal.public_id}"


class TradeItem(models.Model):
    """
    Represents an item transfer within a trade proposal.

    Trade items belong to the transactional trade workflow
    and participate in acceptance, execution, and ownership
    transfer processes. Unlike TradeCycleTrade, these records
    describe exchanges that may eventually be executed.
    """

    proposal = models.ForeignKey(
        TradeProposal,
        on_delete=models.CASCADE,
        related_name="trade_items",
    )

    giver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="items_given",
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="items_received",
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="trade_records",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proposal",
                    "item",
                ],
                name=("unique_item_per_proposal"),
            )
        ]

    def __str__(self):
        return (
            f"{self.giver.username} -> "
            f"{self.receiver.username} "
            f"({self.item.name})"
        )


class TradeCycle(models.Model):
    """
    Represents a discovered multi-party trade cycle.

    A trade cycle contains participating users and
    the item exchanges required to complete the cycle.
    """

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField(
        default=default_cycle_expiry,
    )

    def __str__(self):
        return f"Trade Cycle " f"{self.public_id}"


class TradeCycleParticipant(models.Model):
    """
    Associates a user with a discovered trade cycle.

    This model represents membership within a recommended
    trade cycle and carries no approval or execution state.
    Unlike TradeParticipant, it exists solely to describe
    cycle recommendations generated by the matching engine.
    """

    cycle = models.ForeignKey(
        TradeCycle,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cycle_participations",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cycle",
                    "user",
                ],
                name=("unique_user_per_cycle"),
            )
        ]

    def __str__(self):
        return f"{self.user.username} " f"in {self.cycle.public_id}"


class TradeCycleTrade(models.Model):
    """
    Represents an item exchange within a discovered trade cycle.

    These records describe potential exchanges identified by
    the cycle detection engine. Unlike TradeItem, they do not
    participate in approval, execution, or ownership transfer
    workflows and exist solely as recommendation data.
    """

    cycle = models.ForeignKey(
        TradeCycle,
        on_delete=models.CASCADE,
        related_name="trades",
    )

    giver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cycle_items_given",
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cycle_items_received",
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="cycle_records",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cycle",
                    "item",
                ],
                name=("unique_item_per_cycle"),
            )
        ]

    def __str__(self):
        return (
            f"{self.giver.username} -> "
            f"{self.receiver.username} "
            f"({self.item.name})"
        )
