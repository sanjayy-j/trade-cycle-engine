from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .permissions import IsAdminRole

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