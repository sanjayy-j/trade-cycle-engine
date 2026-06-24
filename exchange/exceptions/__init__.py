"""Domain-specific exceptions raised by the service layer."""


class ItemNotAvailableError(Exception):
    """Raised when a trade proposal references an item that is not AVAILABLE."""


class ProposalNotPendingError(Exception):
    """Raised when an operation requires a PENDING proposal but it is not."""
