from django.urls import path
from .views import (
    profile,
    admin_only,
    ItemListCreateView,
    ItemDetailView,
    WantListCreateView,
    WantDetailView,
    MatchListView,
    DirectTradeView,
    TradeCycleView,
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
    ),

    path(
        "matches/",
        MatchListView.as_view(),
        name="match-list",
    ),

    path(
        "trades/direct/",
        DirectTradeView.as_view(),
        name="direct-trades",
    ),

    path(
        "trades/cycles/",
        TradeCycleView.as_view(),
        name="trade-cycles",
    ),

    path(
        "wants/<int:id>/",
        WantDetailView.as_view(),
        name="want-detail",
    ),
]