from rest_framework import serializers
from goods.models import SKU


class CartSerializer(serializers.Serializer):
    '''购物车参数（sku_id, count, selected）的序列化器'''

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