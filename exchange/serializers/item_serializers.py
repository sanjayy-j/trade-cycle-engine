from rest_framework import serializers

from ..models import Item


class ItemSerializer(serializers.ModelSerializer):
    """Serializes items for read/write; ownership and status are server-controlled."""

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
