from rest_framework.pagination import PageNumberPagination


class CustomPaginator(PageNumberPagination):
    """Кастомный пагинатор."""

    page_size_query_param = 'limit'
