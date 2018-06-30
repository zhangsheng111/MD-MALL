from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
        '''创建分页配置类'''

        page_size = 2  # 如果前端不传参数, 默认每页容量为2
        page_size_query_param = 'page_size'  # 指明前端可以通过page_size参数, 说明每页数量
        max_page_size = 20 # 限制最大每页容量为20