"""Per-endpoint rate throttles, scoped via DEFAULT_THROTTLE_RATES."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class TradeProposalThrottle(UserRateThrottle):
    """Limits how often an authenticated user may create trade proposals."""

    scope = "trade_proposal"


class TradeAcceptanceThrottle(UserRateThrottle):
    """Limits how often an authenticated user may accept/reject proposals."""

    scope = "trade_accept"


class CycleDetectionThrottle(UserRateThrottle):
    """Limits how often an authenticated user may trigger cycle detection."""

    scope = "cycle_detection"


class RegistrationThrottle(AnonRateThrottle):
    """Limits how often an anonymous client may register new accounts."""

    scope = "registration"
