from rest_framework import serializers

from .models import (
    Item,
    TradeCycleParticipant,
    TradeCycleTrade,
    Want,
    TradeProposal,
    TradeParticipant,
    TradeItem,
    TradeCycle,
    TradeExecution,
)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item

        fields = [
            "id",
            "public_id",
            "name",
            "description",
            "status",
            "owner",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "public_id",
            "owner",
            "status",
            "created_at",
            "updated_at",
        ]


class WantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Want

        fields = [
            "id",
            "public_id",
            "user",
            "item",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "public_id",
            "user",
            "created_at",
        ]

    def validate_item(self, value):
        request = self.context["request"]

        if value.owner == request.user:
            raise serializers.ValidationError(
                "You cannot want your own item."
            )

        return value

    def validate(self, attrs):
        request = self.context["request"]

        item = attrs.get(
            "item",
            getattr(self.instance, "item", None)
        )

        existing_want = Want.objects.filter(
            user=request.user,
            item=item,
        )

        if self.instance:
            existing_want = existing_want.exclude(
                id=self.instance.id
            )

        if existing_want.exists():
            raise serializers.ValidationError(
                {
                    "item":
                    "You already want this item."
                }
            )

        return attrs
    
class TradeParticipantSerializer(
    serializers.ModelSerializer
):
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
            "participants",
            "trade_items",
        ]


class TradeExecutionSerializer(
    serializers.ModelSerializer
):
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


class TradeProposalCreateSerializer(
    serializers.Serializer
):
    participants = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )

    trades = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )


class TradeCycleParticipantSerializer(
    serializers.ModelSerializer
):
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
        return obj.participants.count()

    def get_summary(self, obj):
        return f"{self.get_cycle_length(obj)}-way trade cycle found"
