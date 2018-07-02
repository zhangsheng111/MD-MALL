from rest_framework import serializers
from goods.models import SKU


class CartSerializer(serializers.Serializer):
    '''保存购物车商品参数（sku_id, count, selected）的序列化器'''

    sku_id = serializers.IntegerField(label='sku id', min_value=1)
    count = serializers.IntegerField(label='数量',min_value=1)
    selected = serializers.BooleanField(label='是否勾选', default=True)

    def validate(self, attrs):
        try:
            sku = SKU.objects.get(id = attrs['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        if attrs['count'] > sku.stock:
            raise serializers.ValidationError('商品库存不足')

        return attrs



class CartSKUSerializer(serializers.ModelSerializer):
    '''购物车商品数据序列化器'''
    count = serializers.IntegerField(min_value=1)
    selected = serializers.BooleanField(label='是否勾选')

    class Meta:
        model = SKU
        fields = ('id','price', 'name', 'default_image_url', 'count', 'selected')


class CartSKUDeleteSerializer(serializers.Serializer):
    '''删除购物车商品id的序列化器'''
    sku_id = serializers.IntegerField(min_value=1,label='商品id')

    def validate_sku_id(self, value):
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            return serializers.ValidationError('商品不存在')

        return value


class CartSelectAllSerializer(serializers.Serializer):
    '''购物车商品全选选项序列化器'''
    selected = serializers.BooleanField(label='全选')