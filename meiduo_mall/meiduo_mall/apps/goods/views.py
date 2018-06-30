from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from .serializers import SKUSerializer,SKUIndexSerializer
from .models import SKU
from drf_haystack.viewsets import HaystackViewSet

# Create your views here.

class SKUListView(ListAPIView):
    '''sku列表数据（默认/价格/人气）'''
    serializer_class = SKUSerializer
    # 数据来源
    # queryset

    # 排序
    filter_backends = [OrderingFilter]  # 排序过滤器
    ordering_fields = ('create_time', 'price', 'sales')

    # 重写get_queryset()方法，获取不同分类的商品
    def get_queryset(self):
        # 从请求路径中获取分类id
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id = category_id,is_launched = True)  # 上架的才返回显示

    # 分页(dev中配置)、


class SKUSearchViewSet(HaystackViewSet):
    '''SKU关键字搜索'''
    index_models = [SKU]   # SKU数据模型
    serializer_class = SKUIndexSerializer


