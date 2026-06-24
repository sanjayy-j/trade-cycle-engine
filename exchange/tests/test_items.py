from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
)


class ItemApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="sanjay",
            password="test123",
        )

        self.user2 = User.objects.create_user(
            username="murthy",
            password="test123",
        )

        self.client.force_authenticate(
            user=self.user1
        )

    def test_create_item(self):
        response = self.client.post(
            "/api/items/",
            {
                "name": "Keyboard",
                "description": "Mechanical keyboard",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            Item.objects.count(),
            1,
        )

        item = Item.objects.first()

        self.assertEqual(
            item.owner,
            self.user1,
        )

    def test_patch_item(self):
        item = Item.objects.create(
            name="Keyboard",
            description="Old",
            owner=self.user1,
        )

        response = self.client.patch(
            f"/api/items/{item.public_id}/",
            {
                "description": "Updated",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        item.refresh_from_db()

        self.assertEqual(
            item.description,
            "Updated",
        )

    def test_delete_item(self):
        item = Item.objects.create(
            name="Keyboard",
            owner=self.user1,
        )

        response = self.client.delete(
            f"/api/items/{item.public_id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            Item.objects.filter(
                id=item.id
            ).exists()
        )

    def test_non_owner_cannot_patch_item(self):
        item = Item.objects.create(
            name="Keyboard",
            owner=self.user2,
        )

        response = self.client.patch(
            f"/api/items/{item.public_id}/",
            {
                "description": "Hacked",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )
