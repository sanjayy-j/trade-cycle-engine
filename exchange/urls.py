"""URL routes for the exchange app's API endpoints."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    profile,
    admin_only,
    ItemViewSet,
    WantViewSet,
    MatchListView,
    DirectTradeView,
    TradeCycleView,
    TradeHistoryView,
    TradeProposalListCreateView,
    TradeProposalDetailView,
    TradeProposalAcceptView,
    TradeProposalRejectView,
)

# Only true CRUD resources (Item, Want) go through the router. Every
# workflow/action endpoint below stays an explicit path - see
# architecture.md for why.
router = DefaultRouter()
router.register("items", ItemViewSet, basename="item")
router.register("wants", WantViewSet, basename="want")

urlpatterns = [
    path("profile/", profile),
    path("admin-only/", admin_only),

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
        "trade-proposals/",
        TradeProposalListCreateView.as_view(),
        name="trade-proposal-list-create",
    ),

    path(
        "trade-proposals/<uuid:public_id>/",
        TradeProposalDetailView.as_view(),
        name="trade-proposal-detail",
    ),

    path(
        "trade-proposals/<uuid:public_id>/accept/",
        TradeProposalAcceptView.as_view(),
        name="trade-proposal-accept",
    ),

    path(
        "trade-proposals/<uuid:public_id>/reject/",
        TradeProposalRejectView.as_view(),
        name="trade-proposal-reject",
    ),

    path(
        "trade-history/",
        TradeHistoryView.as_view(),
        name="trade-history",
    ),

    path("", include(router.urls)),
]
