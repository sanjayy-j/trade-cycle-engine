from rest_framework import serializers
from .models import Item, Want

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item

        fields = [
            "id",
            "name",
            "description",
            "status",
            "owner",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
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
            "user",
            "item",
            "created_at",
        ]

        read_only_fields = [
            "user",
            "created_at",
        ]

    def validate_item(self, value):
        request = self.context["request"]

        if value.owner == request.user:
            raise serializers.ValidationError(
                "You already have it 😭"
            )
        
        return value