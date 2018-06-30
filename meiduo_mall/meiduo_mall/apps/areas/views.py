from django.shortcuts import render
from rest_framework_extensions.cache.mixins import CacheResponseMixin  # 缓存

from .serializers import AreaSerializer,SubAreaSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Area

# Create your views here.

# 为视图集同时补充List和Retrieve两种缓存，与ListModelMixin和RetrieveModelMixin一起配合使用。
class AreasViewSet(CacheResponseMixin,ReadOnlyModelViewSet):
    '''行政区信息'''
    # 关闭分页
    pagination_class = None

    def get_queryset(self):
        '''提供数据集'''
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        '''提供序列化器'''
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer