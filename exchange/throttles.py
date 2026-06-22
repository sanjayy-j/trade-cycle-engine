from rest_framework.throttling import UserRateThrottle


class TradeProposalThrottle(UserRateThrottle):
    scope = "trade_proposal"


class TradeAcceptanceThrottle(UserRateThrottle):
    scope = "trade_accept"


class CycleDetectionThrottle(UserRateThrottle):
    scope = "cycle_detection"
