"""Shared constants for the exchange app."""

MAX_CYCLE_LENGTH = 5

# Used as the router lookup_value_regex for public_id-keyed ViewSets, so
# a malformed UUID in the URL 404s (no route match) instead of reaching
# the view and raising a ValueError/ValidationError.
UUID_REGEX = (
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
