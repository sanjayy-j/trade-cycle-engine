from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework.decorators import (
    api_view,
    permission_classes,
)

from .pagination import ItemPagination
from .permissions import IsAdminRole, IsOwnerOrAdmin
from .models import (
    User,
    User,
    Item, 
    Want,
    TradeProposal,
    TradeParticipant,
    TradeItem,
    TradeExecution,
)
from .serializers import (
    ItemSerializer,
    WantSerializer, 
    TradeProposalSerializer,
    TradeExecutionSerializer,
    TradeParticipantSerializer,
    TradeItemSerializer,
    TradeProposalCreateSerializer,
    TradeCycleSerializer,
)

from .services import (
    build_trade_graph,
    find_cycles_for_user,
    persist_trade_cycles,
    accept_trade_proposal,
    create_trade_proposal,
)
from .constants import MAX_CYCLE_LENGTH


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response({
        "username": request.user.username,
        "role": request.user.role,
    })


@api_view(["GET"])
@permission_classes([IsAdminRole])
def admin_only(request):
    return Response({
        "message": "Welcome Admin"
    })


class ItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = (
            Item.objects
            .select_related("owner")
            .order_by("created_at")
        )

        paginator = ItemPagination()
        page = paginator.paginate_queryset(items, request)

        serializer = ItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ItemSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
class ItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, public_id):
        try:
            return Item.objects.select_related("owner").get(
                public_id=public_id
            )

        except Item.DoesNotExist:
            return None

    def get(self, request, public_id):
        item = self.get_object(public_id)

        if not item:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ItemSerializer(item)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, public_id):
        item = self.get_object(public_id)

        if not item:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            item,
        ):
            return Response(
                {"error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ItemSerializer(
            item,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, public_id):
        item = self.get_object(public_id)

        if not item:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            item,
        ):
            return Response(
                {"error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        item.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class WantListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wants = (
            Want.objects
            .filter(user=request.user)
            .select_related("user", "item")
        )

        serializer = WantSerializer(
            wants,
            many=True
        )

        return Response(
            serializer.data
        )

    def post(self, request):
        serializer = WantSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save(
                user=request.user
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )  

class WantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, public_id):
        try:
            return Want.objects.select_related(
                "user",
                "item",
            ).get(
                public_id=public_id
            )

        except Want.DoesNotExist:
            return None

    def get(self, request, public_id):
        want = self.get_object(public_id)

        if not want:
            return Response(
                {"error": "Want not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            want,
        ):
            return Response(
                {"error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = WantSerializer(want)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, public_id):
        want = self.get_object(public_id)

        if not want:
            return Response(
                {"error": "Want not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            want,
        ):
            return Response(
                {"error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = WantSerializer(
            want,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, public_id):
        want = self.get_object(public_id)

        if not want:
            return Response(
                {"error": "Want not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            want,
        ):
            return Response(
                {"error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        want.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
    
    
class MatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        results = []

        my_items = (
            Item.objects
            .filter(owner=request.user)
            .prefetch_related(
                "wanted_by__user"
            )
        )

        for item in my_items:
            interested_users = [
                want.user.username
                for want
                in item.wanted_by.all()
            ]

            results.append({
                "item": item.name,
                "interested_users":
                    interested_users,
            })

        return Response(results)

class DirectTradeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        results = []
        seen = set()

        my_items = Item.objects.filter(
            owner=request.user
        )

        my_wants = (
            Want.objects
            .filter(user=request.user)
            .select_related('item', 'item__owner')
        )

        all_matching_wants = (
            Want.objects
            .filter(item__in=my_items)
            .select_related(
                'user',
                'item',
                'item__owner',
            )
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
                for match in wants_by_user[
                    other_user.id
                ]:
                    trade_key = (
                        other_user.id,
                        match.item.id,
                        target_item.id,
                    )

                    if trade_key not in seen:
                        seen.add(trade_key)

                        results.append({
                            "with_user":
                                other_user.username,
                            "your_item":
                                match.item.name,
                            "their_item":
                                target_item.name,
                        })

        return Response(results)


class TradeCycleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        executions = (
            TradeExecution.objects
            .filter(
                proposal__participants__user=request.user
            )
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
    
class TradeProposalListCreateView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
    ):
        proposals = (
            TradeProposal.objects
            .filter(
                participants__user=request.user
            )
            .distinct()
            .prefetch_related(
                "participants__user",
                "trade_items__item",
                "trade_items__giver",
                "trade_items__receiver",
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = (
            TradeProposalSerializer(
                proposals,
                many=True,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
    
    def post(
        self,
        request,
    ):
        serializer = (
            TradeProposalCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        participant_ids = (
            serializer.validated_data[
                "participants"
            ]
        )

        trade_data = (
            serializer.validated_data[
                "trades"
            ]
        )

        if request.user.id not in participant_ids:
            return Response(
                {
                    "error":
                    "You must be part of the trade"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        participants = list(
            User.objects.filter(
                id__in=participant_ids
            )
        )

        item_ids = {
            trade["item"]
            for trade in trade_data
        }
        user_ids = {
            trade["giver"]
            for trade in trade_data
        } | {
            trade["receiver"]
            for trade in trade_data
        }

        items = {
            item.id: item
            for item in Item.objects.filter(
                id__in=item_ids
            )
        }
        users = {
            user.id: user
            for user in User.objects.filter(
                id__in=user_ids
            )
        }

        if len(items) != len(item_ids):
            raise Item.DoesNotExist

        if len(users) != len(user_ids):
            raise User.DoesNotExist

        trades = []

        for trade in trade_data:
            trades.append(
                {
                    "item": items[trade["item"]],
                    "giver": users[trade["giver"]],
                    "receiver": users[trade["receiver"]],
                }
            )

        proposal = create_trade_proposal(
            participants,
            trades,
        )

        serializer = (
            TradeProposalSerializer(
                proposal
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    
class TradeProposalDetailView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        public_id,
    ):
        try:
            proposal = (
                TradeProposal.objects
                .prefetch_related(
                    "participants__user",
                    "trade_items__item",
                    "trade_items__giver",
                    "trade_items__receiver",
                )
                .get(
                    public_id=public_id
                )
            )

        except TradeProposal.DoesNotExist:
            return Response(
                {
                    "error":
                    "Trade proposal not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            TradeProposalSerializer(
                proposal
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
    
    
class TradeProposalAcceptView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        public_id,
    ):
        try:
            proposal = (
                TradeProposal.objects
                .prefetch_related(
                    "participants__user",
                    "trade_items__item",
                    "trade_items__giver",
                    "trade_items__receiver",
                )
                .get(
                    public_id=public_id
                )
            )

        except TradeProposal.DoesNotExist:
            return Response(
                {
                    "error":
                    "Trade proposal not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        participant_exists = any(
            participant.user_id == request.user.id
            for participant in proposal.participants.all()
        )

        if not participant_exists:
            return Response(
                {
                    "error":
                    "You are not part "
                    "of this trade"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        accept_trade_proposal(
            proposal,
            request.user,
        )

        proposal.refresh_from_db()

        serializer = (
            TradeProposalSerializer(
                proposal
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )