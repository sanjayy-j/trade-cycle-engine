from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework.decorators import (
    api_view,
    permission_classes,
)

from .permissions import IsAdminRole, IsOwnerOrAdmin
from .models import Item, Want
from .serializers import (
    ItemSerializer,
    WantSerializer, 
)

from .services import (
    build_trade_graph,
    find_cycles_for_user,
)


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
        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)

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

    def get(self, request, id):
        try:
            item = Item.objects.get(id=id)

        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ItemSerializer(item)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        ) 
    
    def patch(self, request, id):
        try:
            item = Item.objects.get(id=id)

        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            item
        ):
            return Response(
                {"error": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ItemSerializer(
            item,
            data=request.data,
            partial=True
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
    
    def delete(self, request, id):
        try:
            item = Item.objects.get(id=id)

        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = IsOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            item
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
        wants = Want.objects.filter(
            user=request.user
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
    
    
class MatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        results = []

        my_items = Item.objects.filter(
            owner=request.user
        )

        for item in my_items:
            wants = Want.objects.filter(
                item = item
            )

            interested_users = [
                want.user.username
                for want in wants
            ]
        
            results.append({
                "item": item.name,
                "interested_users": interested_users,
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

        my_wants = Want.objects.filter(
            user=request.user
        )

        for want in my_wants:
            target_item = want.item
            other_user = target_item.owner

            matching_wants = Want.objects.filter(
                user=other_user,
                item__in=my_items
            )

            for match in matching_wants:
                trade_key = (
                    other_user.id,
                    match.item.id,
                    target_item.id,
                )

                if trade_key not in seen:
                    seen.add(trade_key)

                    results.append({
                        "with_user": other_user.username,
                        "your_item": match.item.name,
                        "their_item": target_item.name,
                    })

        return Response(results)


class TradeCycleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        graph = build_trade_graph()

        cycles = find_cycles_for_user(
            graph,
            request.user.id,
            max_depth=5,
        )

        response = []

        for cycle in cycles:
            response.append({
                "cycle_length":
                    cycle["cycle_length"],

                "summary":
                    f"{cycle['cycle_length']}-way trade cycle found",

                "participants": [
                    user.username
                    for user
                    in cycle["participants"]
                ],

                "trades": [
                    {
                        "giver":
                            trade["giver"].username,

                        "receiver":
                            trade["receiver"].username,

                        "item":
                            trade["item"].name,
                    }
                    for trade
                    in cycle["trades"]
                ],
            })

        return Response(
            response,
            status=status.HTTP_200_OK,
        )