"""
タスク管理API - カスタムペジネーション
OpenAPI仕様書に基づくページネーション設定
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """カスタムページネーション"""
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'pagination': {
                'currentPage': self.page.number,
                'totalPages': self.page.paginator.num_pages,
                'totalItems': self.page.paginator.count,
                'itemsPerPage': self.get_page_size(self.request),
                'hasNext': self.page.has_next(),
                'hasPrev': self.page.has_previous(),
            }
        })
