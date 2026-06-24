from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


class HealthView(APIView):
    """
    Unauthenticated liveness/readiness check.

    Confirms the application is running and can reach the database.
    Intended for load balancers / container orchestrators, not for
    detailed diagnostics.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        """Return 200 with database status ok, or 503 if the database is unreachable."""
        try:
            connection.ensure_connection()
            database_ok = True
        except Exception:
            database_ok = False

        body = {
            "status": "ok" if database_ok else "error",
            "database": "ok" if database_ok else "unreachable",
        }

        response_status = (
            status.HTTP_200_OK
            if database_ok
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return Response(body, status=response_status)


class VersionView(APIView):
    """Unauthenticated endpoint reporting the running API version."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        """Return the configured API_VERSION, or "unknown" if it is not set."""
        return Response(
            {"version": getattr(settings, "API_VERSION", "unknown")},
            status=status.HTTP_200_OK,
        )
