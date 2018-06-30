import base64
import pickle
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializer import CartSerializer
from . import constants


class CartView(GenericAPIView):
    '''添加购物车商品'''
    serializer_class = CartSerializer

    def perform_authentication(self, request):
        '''重写父类APIView方法， 在进入视图前,不验证JWT '''
        pass


    def post(self,request):
        # 获取参数（sku_id, count, selected）
        # 校验参数
        # 传入参数反序列化验证
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.data['sku_id']
        count = serializer.data['count']
        selected = serializer.data['selected']


        # 尝试验证用户是否登陆(捕获异常处理)
        try:
            user = request.user
        except Exception:
            # 验证失败，未登陆
            user = None

        # 保存:用户登陆保存到redis
        if user and user.is_authenticated: # 用户存在并且通过验证双重验证
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hincrby('cart_%s' % user.id, sku_id, count)# 累加保存购物车商品数量（哈希）
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)  # 把勾选的商品id保存到set集合（去重）

            # 管道
            pl.execute()
            return Response(serializer.data)


        # 保存: 用户未登录保存到cookie(# 保存cookie涉及到Response,不能在序列化器中操作)
        else:
            # 先从cookie中获取数据，看是否有购物车记录
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 购物车记录存在，解析出来
                cart_bytes = base64.b64decode(cart_str)
                cart = pickle.loads(cart_bytes)
            else:
                # cookie中不存在购物车记录
                cart = {}

            # 更新已存在的购物车记录中的信息
            sku = cart.get('sku_id')
            if sku:
                # 商品已经加入过购物车
                sku[sku_id]['count'] = sku[sku_id]['count'] + count  # 再加入购物车，就累加商品数量
                sku[sku_id]['selected'] = selected  # 更新是否勾选状态
            else:
                # 商品没有加入过购物车,就添加进去
                cart[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            # 更新信息后需要再转化成cookie支持的字符串格式
            cart_bytes = pickle.dumps(cart)
            cart_str = base64.b64encode(cart_bytes)

            # 返回结果
            response = Response(serializer.data)                    # 有效期
            response.set_cookie('cart', cart_str, max_age=constants.CART_COOKIE_EXPIRES)
            return response