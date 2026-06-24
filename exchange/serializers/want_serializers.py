from rest_framework import serializers

from ..models import Item, Want


class WantSerializer(serializers.ModelSerializer):
    """Serializes wants, rejecting self-wants and duplicate user/item pairs."""

    # Overrides the implicit field so soft-deleted items can't be wanted;
    # the model's default manager (used for the auto-generated field)
    # intentionally stays unfiltered for historical FK lookups.
    item = serializers.PrimaryKeyRelatedField(queryset=Item.active.all())

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
        """Reject wanting an item the requesting user already owns."""
        request = self.context["request"]

        if value.owner == request.user:
            raise serializers.ValidationError(
                "You cannot want your own item."
            )

        return value

    def validate(self, attrs):
        """Reject creating/updating a want that would duplicate an existing one."""
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
