from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import (
    User,
    Item,
    Want,
)

class WantApiTests(TestCase):

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

        self.user3 = User.objects.create_user(
            username="kavin",
            password="test123",
        )

        self.item1 = Item.objects.create(
            name="Keyboard",
            owner=self.user1,
        )

        self.item2 = Item.objects.create(
            name="Laptop",
            owner=self.user2,
        )

        self.item3 = Item.objects.create(
            name="Monitor",
            owner=self.user3,
        )

        self.client.force_authenticate(
            user=self.user1
        )

    def test_create_want(self):
        response = self.client.post(
            "/api/wants/",
            {
                "item": self.item2.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            Want.objects.count(),
            1,
        )

    def test_reject_self_want(self):
        response = self.client.post(
            "/api/wants/",
            {
                "item": self.item1.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Want.objects.count(),
            0,
        )

    def test_reject_duplicate_want(self):
        Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        response = self.client.post(
            "/api/wants/",
            {
                "item": self.item2.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_delete_want(self):
        want = Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        response = self.client.delete(
            f"/api/wants/{want.id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            Want.objects.filter(
                id=want.id
            ).exists()
        )

    def test_patch_want(self):
        want = Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        response = self.client.patch(
            f"/api/wants/{want.id}/",
            {
                "item": self.item3.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        want.refresh_from_db()

        self.assertEqual(
            want.item,
            self.item3,
        )
        
    def test_patch_want_rejects_own_item(self):
        want = Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        response = self.client.patch(
            f"/api/wants/{want.id}/",
            {
                "item": self.item1.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_patch_want_rejects_duplicate(self):
        want1 = Want.objects.create(
            user=self.user1,
            item=self.item2,
        )

        want2 = Want.objects.create(
            user=self.user1,
            item=self.item3,
        )

        response = self.client.patch(
            f"/api/wants/{want2.id}/",
            {
                "item": self.item2.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )