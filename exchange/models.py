from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Item(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        TRADED = "TRADED", "Traded"

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

