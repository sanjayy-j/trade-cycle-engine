from rest_framework import serializers
from .models import Item

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