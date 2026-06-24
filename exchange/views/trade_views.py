from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ..throttles import CycleDetectionThrottle
from ..models import Item, Want, TradeExecution
from ..serializers import TradeCycleSerializer, TradeExecutionSerializer
from ..services import (
    build_trade_graph,
    find_cycles_for_user,
    persist_trade_cycles,
)
from ..constants import MAX_CYCLE_LENGTH


class DirectTradeView(APIView):
    """Finds direct (2-party) trade matches: users who each want the other's item."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return pairwise matches between the user's wants and others' wants."""
        results = []
        seen = set()

        my_items = Item.objects.filter(owner=request.user)

        my_wants = Want.objects.filter(user=request.user).select_related(
            "item", "item__owner"
        )

        all_matching_wants = Want.objects.filter(item__in=my_items).select_related(
            "user",
            "item",
            "item__owner",
        )

        wants_by_user = {}
        for want in all_matching_wants:
            if want.user.id not in wants_by_user:
                wants_by_user[want.user.id] = []
            wants_by_user[want.user.id].append(want)

        for want in my_wants:
            target_item = want.item
            other_user = target_item.owner

            if other_user.id in wants_by_user:
                for match in wants_by_user[other_user.id]:
                    trade_key = (
                        other_user.id,
                        match.item.id,
                        target_item.id,
                    )

                    if trade_key not in seen:
                        seen.add(trade_key)

                        results.append(
                            {
                                "with_user": other_user.username,
                                "your_item": match.item.name,
                                "their_item": target_item.name,
                            }
                        )

        return Response(results)


class TradeCycleView(APIView):
    """
    Returns trade cycle recommendations for the
    authenticated user.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [CycleDetectionThrottle]

    def get(self, request):
        """Detect, persist, and return trade cycles involving the requesting user."""
        graph = build_trade_graph()

        cycles = find_cycles_for_user(
            graph,
            request.user.id,
            max_depth=MAX_CYCLE_LENGTH,
        )

        persisted_cycles = persist_trade_cycles(cycles)

        serializer = TradeCycleSerializer(
            persisted_cycles,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class TradeHistoryView(APIView):
    """
    Provides execution history for trades involving
    the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return executed trades the requesting user participated in, newest first."""
        executions = (
            TradeExecution.objects.filter(proposal__participants__user=request.user)
            .distinct()
            .select_related("proposal")
            .prefetch_related(
                "proposal__participants__user",
                "proposal__trade_items__item",
                "proposal__trade_items__giver",
                "proposal__trade_items__receiver",
            )
            .order_by("-executed_at")
        )

        serializer = TradeExecutionSerializer(
            executions,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
