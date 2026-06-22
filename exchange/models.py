import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


def default_cycle_expiry():
    return timezone.now() + timedelta(hours=24)


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )


class Item(models.Model):

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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "item"],
                name="unique_user_item_want"
            )
        ]

    def __str__(self):
        return f"{self.user.username} wants {self.item.name}"


class TradeProposal(models.Model):

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

    def __str__(self):
        return (
            f"Trade Proposal "
            f"{self.public_id}"
        )
    
class TradeParticipant(models.Model):

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
                name=(
                    "unique_user_per_proposal"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} "
            f"in {self.proposal.public_id}"
        )
    
class TradeItem(models.Model):

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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proposal",
                    "item",
                ],
                name=(
                    "unique_item_per_proposal"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.giver.username} -> "
            f"{self.receiver.username} "
            f"({self.item.name})"
        )
    

class TradeCycle(models.Model):

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
        return (
            f"Trade Cycle "
            f"{self.public_id}"
        )


class TradeCycleParticipant(models.Model):

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
                name=(
                    "unique_user_per_cycle"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} "
            f"in {self.cycle.public_id}"
        )


class TradeCycleTrade(models.Model):

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
                name=(
                    "unique_item_per_cycle"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.giver.username} -> "
            f"{self.receiver.username} "
            f"({self.item.name})"
        )