from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView

from ..serializers import RegisterSerializer, RegisterResponseSerializer
from ..throttles import RegistrationThrottle


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    """Return the authenticated user's username and role."""
    return Response(
        {
            "username": request.user.username,
            "role": request.user.role,
        }
    )


class RegisterView(APIView):
    """
    Public registration endpoint. Always creates the new user with the
    default USER role - the request body has no field through which a
    caller could request ADMIN.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RegistrationThrottle]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterResponseSerializer},
    )
    def post(self, request):
        """Validate and create a new user, returning a 201 on success."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "User registered successfully."},
            status=status.HTTP_201_CREATED,
        )
