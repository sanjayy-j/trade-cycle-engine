from django.urls import path
from .views import (
    profile,
    admin_only,
    ItemListCreateView,
    ItemDetailView,
    WantListCreateView
)

urlpatterns = [
    path("profile/", profile),
    path("admin-only/", admin_only),

    path(
        "items/",
        ItemListCreateView.as_view(),
        name="item-list-create",
    ),

    path(
        "items/<int:id>/",
        ItemDetailView.as_view(),
        name="item-detail",
    ),

    path(
        "wants/",
        WantListCreateView.as_view(),
        name="want-list-create",
    )
]