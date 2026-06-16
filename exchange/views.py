from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rest_framework.decorators import (
    api_view,
    permission_classes,
)

from .permissions import IsAdminRole, IsOwnerOrAdmin
from .models import Item
from .serializers import (
    ItemSerializer,
    WantSerializer, 
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
            {"message": "Item deleted successfully"},
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


