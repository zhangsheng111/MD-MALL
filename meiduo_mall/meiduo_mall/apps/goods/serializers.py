from goods.search_indexes import SKUIndex
from .models import SKU
from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer


class SKUSerializer(serializers.ModelSerializer):
    '''list.html 按分类区分的商品列表序列化器'''
    class Meta:
        model = SKU
        fields = ('id','name','price','default_image_url','comments')



class SKUIndexSerializer(HaystackSerializer):
    '''索引结果数据序列化器'''
    class Meta:
        index_classes = [SKUIndex]
        fields = ('text','id','name','price','default_image_url','comments') # 和索引类的字段一致
