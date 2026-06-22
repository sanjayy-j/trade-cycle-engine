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
    TradeHistoryView,
    TradeProposalListCreateView,
    TradeProposalDetailView,
    TradeProposalAcceptView,
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
        "items/<uuid:public_id>/",
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
        "wants/<uuid:public_id>/",
        WantDetailView.as_view(),
        name="want-detail",
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
        "trade-history/",
        TradeHistoryView.as_view(),
        name="trade-history",
    ),
]