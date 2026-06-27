"""Project-level URL routes: admin, auth, API schema, and the exchange app."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from exchange.views import HealthView, VersionView, RegisterView


urlpatterns = [
    path("admin/", admin.site.urls),

    path("health/", HealthView.as_view(), name="health"),
    path("version/", VersionView.as_view(), name="version"),

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    path(
        "api/auth/register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "api/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path("api/", include("exchange.urls"))
]
