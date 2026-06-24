from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ..models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Public registration serializer.

    ``role`` is intentionally excluded from the field list, so a
    registration request has no way to request anything other than the
    model's default USER role.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        """Reject the email if it is already registered to another account."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_password(self, value):
        """Run Django's configured password validators against the raw password."""
        try:
            django_validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

        return value

    def create(self, validated_data):
        """Create the new user, forcing the default USER role."""
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.USER,
        )


class RegisterResponseSerializer(serializers.Serializer):
    """Documents the response shape of RegisterView for OpenAPI."""

    message = serializers.CharField()
