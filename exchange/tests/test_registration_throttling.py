from django.core.cache import cache
from django.test import TestCase

from rest_framework.test import APIClient


class RegistrationThrottlingTests(TestCase):

    def setUp(self):
        # RegistrationThrottle is IP-keyed, and the Django test client
        # always reports the same IP, so the throttle cache must be
        # cleared per test - otherwise requests made by earlier tests
        # (or test_registration.py) would count against this test's
        # quota.
        cache.clear()

        self.client = APIClient()

    def register(self, index):
        return self.client.post(
            "/api/auth/register/",
            {
                "username": f"throttleuser{index}",
                "email": f"throttleuser{index}@example.com",
                "password": "S0meStrongPassword!",
            },
            format="json",
        )

    def test_registration_rate_limit_returns_429(self):
        for i in range(11):
            response = self.register(i)

            if i < 10:
                self.assertEqual(
                    response.status_code,
                    201,
                    msg=f"request {i} should have succeeded",
                )
            else:
                self.assertEqual(
                    response.status_code,
                    429,
                    msg="11th request within the hour should be throttled",
                )
