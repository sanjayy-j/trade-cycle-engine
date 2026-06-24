from rest_framework import serializers

from ..models import (
    Item,
    TradeCycle,
    TradeCycleParticipant,
    TradeCycleTrade,
    TradeExecution,
    TradeItem,
    TradeParticipant,
    TradeProposal,
    User,
)


class TradeParticipantSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a participant's acceptance state within a proposal."""

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = TradeParticipant

        fields = [
            "username",
            "accepted",
            "accepted_at",
        ]


class TradeItemSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a single giver/receiver/item leg of a trade proposal."""

    giver = serializers.CharField(
        source="giver.username",
        read_only=True,
    )

    receiver = serializers.CharField(
        source="receiver.username",
        read_only=True,
    )

    item = serializers.CharField(
        source="item.name",
        read_only=True,
    )

    class Meta:
        model = TradeItem

        fields = [
            "giver",
            "receiver",
            "item",
        ]


class TradeProposalSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a trade proposal with its participants and trade legs."""

    participants = (
        TradeParticipantSerializer(
            many=True,
            read_only=True,
        )
    )

    trade_items = (
        TradeItemSerializer(
            many=True,
            read_only=True,
        )
    )

    class Meta:
        model = TradeProposal

        fields = [
            "public_id",
            "status",
            "created_at",
            "updated_at",
            "expires_at",
            "participants",
            "trade_items",
        ]


class TradeExecutionSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a completed trade execution, with its source proposal."""

    proposal_public_id = serializers.CharField(
        source="proposal.public_id",
        read_only=True,
    )
    proposal_status = serializers.CharField(
        source="proposal.status",
        read_only=True,
    )
    participants = TradeParticipantSerializer(
        source="proposal.participants",
        many=True,
        read_only=True,
    )
    trade_items = TradeItemSerializer(
        source="proposal.trade_items",
        many=True,
        read_only=True,
    )

    class Meta:
        model = TradeExecution

        fields = [
            "public_id",
            "executed_at",
            "proposal_public_id",
            "proposal_status",
            "participants",
            "trade_items",
        ]


class TradeSerializer(serializers.Serializer):
    """
    Validates a single giver/receiver/item leg of a trade proposal.

    Resolves ``giver``, ``receiver``, and ``item`` to their model
    instances (404-style "does not exist" errors surface as field-level
    400s if the ids are invalid), and rejects a giver and receiver being
    the same user.
    """

    giver = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    receiver = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    item = serializers.PrimaryKeyRelatedField(
        queryset=Item.active.all(),
    )

    def validate(self, attrs):
        """Reject a trade leg where the giver and receiver are the same user."""
        if attrs["giver"] == attrs["receiver"]:
            raise serializers.ValidationError(
                "giver and receiver must be different users."
            )

        return attrs


class TradeProposalCreateSerializer(
    serializers.Serializer
):
    """
    Validates the payload for creating a multi-party trade proposal.

    Ensures every trade's giver and receiver are part of the overall
    ``participants`` list, since a user's item should never move without
    that user being a participant who must approve the trade.
    """

    participants = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )

    trades = TradeSerializer(
        many=True,
        allow_empty=False,
    )

    def validate(self, attrs):
        """Reject the payload if any trade's giver/receiver isn't a listed participant."""
        participant_ids = set(attrs["participants"])

        non_participants = set()

        for trade in attrs["trades"]:
            if trade["giver"].id not in participant_ids:
                non_participants.add(trade["giver"].id)

            if trade["receiver"].id not in participant_ids:
                non_participants.add(trade["receiver"].id)

        if non_participants:
            raise serializers.ValidationError(
                {
                    "trades": (
                        "Every giver and receiver must be a participant "
                        "in the trade. Invalid user ids: "
                        f"{sorted(non_participants)}"
                    )
                }
            )

        return attrs


class TradeCycleParticipantSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a user's membership in a discovered trade cycle."""

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = TradeCycleParticipant

        fields = [
            "username",
        ]


class TradeCycleTradeSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a single recommended exchange within a trade cycle."""

    giver = serializers.CharField(
        source="giver.username",
        read_only=True,
    )

    receiver = serializers.CharField(
        source="receiver.username",
        read_only=True,
    )

    item = serializers.CharField(
        source="item.name",
        read_only=True,
    )

    class Meta:
        model = TradeCycleTrade

        fields = [
            "giver",
            "receiver",
            "item",
        ]


class TradeCycleSerializer(
    serializers.ModelSerializer
):
    """Read-only view of a discovered trade cycle, with a human-readable summary."""

    participants = (
        TradeCycleParticipantSerializer(
            many=True,
            read_only=True,
        )
    )

    trades = (
        TradeCycleTradeSerializer(
            many=True,
            read_only=True,
        )
    )

    cycle_length = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = TradeCycle

        fields = [
            "public_id",
            "active",
            "created_at",
            "expires_at",
            "participants",
            "trades",
            "cycle_length",
            "summary",
        ]

    def get_cycle_length(self, obj):
        """Return the number of distinct participants in the cycle."""
        return obj.participants.count()

    def get_summary(self, obj):
        """Return a short human-readable description of the cycle's size."""
        return f"{self.get_cycle_length(obj)}-way trade cycle found"
