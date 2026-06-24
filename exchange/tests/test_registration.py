from django.core.cache import cache
from django.test import TestCase

from rest_framework.test import APIClient

from exchange.models import User


class RegistrationApiTests(TestCase):

    def setUp(self):
        # RegistrationThrottle is IP-keyed, and the Django test client
        # always reports the same IP, so the throttle cache must be
        # cleared per test to keep these tests independent of each
        # other (and of test_registration_throttling.py).
        cache.clear()

        self.client = APIClient()

    def register(self, **overrides):
        payload = {
            "username": "sanjay",
            "email": "sanjay@example.com",
            "password": "S0meStrongPassword!",
        }
        payload.update(overrides)

        return self.client.post(
            "/api/auth/register/",
            payload,
            format="json",
        )

    def test_successful_registration(self):
        response = self.register()

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data,
            {"message": "User registered successfully."},
        )

        self.assertTrue(
            User.objects.filter(username="sanjay").exists()
        )

    def test_role_defaults_to_user(self):
        # Registration has no field through which a caller could request
        # ADMIN, so every new account must default to USER.
        self.register()

        user = User.objects.get(username="sanjay")

        self.assertEqual(
            user.role,
            User.Role.USER,
        )

    def test_duplicate_username_rejected(self):
        User.objects.create_user(
            username="sanjay",
            email="other@example.com",
            password="test123456!",
        )

        response = self.register()

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn("username", response.data)

    def test_registered_user_can_login(self):
        self.register()

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "sanjay",
                "password": "S0meStrongPassword!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_token_refresh(self):
        self.register()

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "sanjay",
                "password": "S0meStrongPassword!",
            },
            format="json",
        )

        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
