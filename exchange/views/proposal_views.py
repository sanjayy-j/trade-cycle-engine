from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ..throttles import TradeProposalThrottle, TradeAcceptanceThrottle
from ..models import User, TradeProposal
from ..serializers import TradeProposalSerializer, TradeProposalCreateSerializer
from ..services import (
    accept_trade_proposal,
    create_trade_proposal,
    reject_trade_proposal,
    expire_trade_proposal_if_needed,
    ItemNotAvailableError,
    ProposalNotPendingError,
)


class TradeProposalListCreateView(APIView):
    """
    Lists trade proposals involving the authenticated user
    and creates new multi-party trade proposals.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [TradeProposalThrottle]

    def get(
        self,
        request,
    ):
        """Return the requesting user's trade proposals, newest first."""
        proposals = (
            TradeProposal.objects.filter(participants__user=request.user)
            .distinct()
            .prefetch_related(
                "participants__user",
                "trade_items__item",
                "trade_items__giver",
                "trade_items__receiver",
            )
            .order_by("-created_at")
        )

        serializer = TradeProposalSerializer(
            proposals,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request,
    ):
        """Validate and create a multi-party trade proposal for its participants."""
        serializer = TradeProposalCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        participant_ids = serializer.validated_data["participants"]

        trade_data = serializer.validated_data["trades"]

        if request.user.id not in participant_ids:
            return Response(
                {"error": "You must be part of the trade"},
                status=status.HTTP_403_FORBIDDEN,
            )

        participants = list(User.objects.filter(id__in=participant_ids))

        trades = [
            {
                "item": trade["item"],
                "giver": trade["giver"],
                "receiver": trade["receiver"],
            }
            for trade in trade_data
        ]

        try:
            proposal = create_trade_proposal(
                participants,
                trades,
            )
        except ItemNotAvailableError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TradeProposalSerializer(proposal)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


def _get_accessible_proposal(public_id, user):
    """
    Fetches a trade proposal by public_id and confirms the user is one
    of its participants.

    Returns:
        (proposal, None) on success, or (None, error_response) if the
        proposal doesn't exist or the user isn't a participant.
    """
    try:
        proposal = TradeProposal.objects.prefetch_related(
            "participants__user",
            "trade_items__item",
            "trade_items__giver",
            "trade_items__receiver",
        ).get(public_id=public_id)
    except TradeProposal.DoesNotExist:
        return None, Response(
            {"error": "Trade proposal not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    is_participant = any(
        participant.user_id == user.id
        for participant in proposal.participants.all()
    )

    if not is_participant:
        return None, Response(
            {"error": "You are not part of this trade"},
            status=status.HTTP_403_FORBIDDEN,
        )

    return proposal, None


class TradeProposalDetailView(APIView):
    """Retrieves a single trade proposal the requesting user participates in."""

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        public_id,
    ):
        """Return the proposal, lazily expiring it first if it is overdue."""
        proposal, error = _get_accessible_proposal(public_id, request.user)

        if error:
            return error

        expire_trade_proposal_if_needed(proposal)

        serializer = TradeProposalSerializer(proposal)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class TradeProposalAcceptView(APIView):
    """
    Allows trade participants to accept a proposal
    and trigger execution once unanimous approval is reached.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [TradeAcceptanceThrottle]

    def post(
        self,
        request,
        public_id,
    ):
        """Record the user's acceptance, executing the trade if now unanimous."""
        proposal, error = _get_accessible_proposal(public_id, request.user)

        if error:
            return error

        try:
            accept_trade_proposal(
                proposal,
                request.user,
            )
        except ProposalNotPendingError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        proposal.refresh_from_db()

        serializer = TradeProposalSerializer(proposal)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class TradeProposalRejectView(APIView):
    """
    Allows any trade participant to reject a pending proposal,
    cancelling it for all participants and releasing reserved items.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [TradeAcceptanceThrottle]

    def post(
        self,
        request,
        public_id,
    ):
        """Reject the proposal on the user's behalf, cancelling it for everyone."""
        proposal, error = _get_accessible_proposal(public_id, request.user)

        if error:
            return error

        try:
            reject_trade_proposal(
                proposal,
                request.user,
            )
        except ProposalNotPendingError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = TradeProposalSerializer(proposal)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
