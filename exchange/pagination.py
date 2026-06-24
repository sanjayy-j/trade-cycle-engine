"""Pagination classes for exchange API list endpoints."""

from rest_framework.pagination import PageNumberPagination


class ItemPagination(PageNumberPagination):
    """Page-number pagination for item listings, with a client-tunable page size."""

    page_size = 10

    page_size_query_param = "page_size"

    max_page_size = 100
