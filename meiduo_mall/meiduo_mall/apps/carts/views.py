import base64
import pickle
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializer import CartSerializer,CartSKUSerializer,CartSKUDeleteSerializer,CartSelectAllSerializer
from . import constants
from goods.models import SKU


class CartView(GenericAPIView):
    '''购物车商品操作'''
    serializer_class = CartSerializer

    def perform_authentication(self, request):
        '''重写父类APIView方法， 在进入视图前,不验证JWT '''
        pass

    def post(self,request):
        '''添加购物车商品'''
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
                cart_bytes = base64.b64decode(cart_str.encode())
                cart_dict = pickle.loads(cart_bytes)
            else:
                # cookie中不存在购物车记录
                cart_dict = {}

            # 更新已存在的购物车记录中的信息
            sku = cart_dict.get('sku_id')
            if sku:
                # 商品已经加入过购物车
                sku[sku_id]['count'] = sku[sku_id]['count'] + count  # 再加入购物车，就累加商品数量
                sku[sku_id]['selected'] = selected  # 更新是否勾选状态
            else:
                # 商品没有加入过购物车,就添加进去
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            # 更新信息后需要再转化成cookie支持的字符串格式
            cart_bytes = pickle.dumps(cart_dict)
            cart_str = base64.b64encode(cart_bytes).decode()

            # 返回结果
            response = Response(serializer.data)                    # 有效期
            response.set_cookie('cart', cart_str, max_age=constants.CART_COOKIE_EXPIRES)
            return response

    def get(self,request):
        '''查询显示购物车商品'''

        # 判断是否登陆
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果已登陆， 获取redis中的存储的商品
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id,)   # 获取user_id: count
            # redis_cart = {
            #     商品sku_id  bytes字节类型:  商品数量  bytes字节类型
            #     商品sku_id  bytes字节类型:  商品数量  bytes字节类型
            # ...
            # }
            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id) # 获取user_id = set(suk_id)
            # user_id =(sku_id1, sku_id2...)
            # 把哈希和集合融合起来形成新的字典
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_selected # 在为True或不在为False
                }

        else:
            # 如果未登陆， 获取cookie中存储的商品
            cookie_cart_str = request.COOKIES.get('cart')

            if cookie_cart_str:
                # 表示cookie中有购物车记录（把字符串解析成字典）
                cart_bytes = cookie_cart_str.encode()
                cart_data = base64.b64decode(cart_bytes)
                cart_dict = pickle.loads(cart_data)
            else:
                # 表示没有购物车记录
                cart_dict = {}
            # cookie_cart_dict = {
            #     sku_id: {
            #         count: 10
            #         selected: True
            #     },
            #     sku_id: {
            #         count: 20
            #         selected: False
            #     }
            # }

        # 从数据库获取数据
        sku_id_list = cart_dict.keys()  # 商品id列表
        sku_obj_list = SKU.objects.filter(id__in = sku_id_list)
        # 补充count和selected属性
        for sku in sku_obj_list:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 序列化返回
        serializer = CartSKUSerializer(sku_obj_list,many=True)
        return Response(serializer.data)

    def put(self,request):
        '''修改购物车商品数据'''
        # 获取商品id 数量和是否勾选
        # 传入参数反序列化验证
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.data['sku_id']
        count = serializer.data['count']
        selected = serializer.data['selected']

        # 判断用户是否登陆
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果已登陆, 修改数据后保存到redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 修改商品数量
            pl.hset('cart_%s' % user.id, sku_id, count)

            if selected:
                # 勾选
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 取消勾选
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            # 返回数据
            return Response(serializer.data)

        else:
            # 如果未登陆, 修改数据后保存到cookie
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            # cart_dict = {
            #     sku_id: {
            #         count: 10
            #         selected: True
            #     },
            #     sku_id: {
            #         count: 20
            #         selected: False
            #     }
            # }
            # 如果修改的商品在购物车中则修改其数量和是否勾选。
            if sku_id in cart_dict.keys():
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            # 转成cookie中的字符串
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = Response(serializer.data)
            response.set_cookie('cart', cart_str, max_age=constants.CART_COOKIE_EXPIRES) # 有效期365天
            # 返回数据
            return response


    def delete(self, request):
        '''删除购物车商品'''

        # 获取参数sku_id
        # 序列化器校验参数
        serializer = CartSKUDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']

        # 判断是否登陆
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 用户已登陆， 删除redis中的商品
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 删除hash中的数据
            pl.hdel('cart_%s' % user.id, sku_id)  # 删除指定的商品的键即删除该商品
            # 删除set中的数据
            pl.srem('cart_selected_%s' % user.id, sku_id)  # 把该商品id从勾选集合中删除
            pl.execute()

            return Response(serializer.data)

        else:
            # 用户未登陆删除cookie中的商品
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 先解析成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            # cart_dict = {
            #     sku_id: {
            #         count: 10
            #         selected: True
            #     },
            #     sku_id: {
            #         count: 20
            #         selected: False
            #     }
            # }
            response = Response(status=status.HTTP_204_NO_CONTENT)
            if sku_id in cart_dict:
                del cart_dict[sku_id]
                # 转换成字符串
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('cart', cart_str, constants.CART_COOKIE_EXPIRES)

            return response


class CartSelectAllView(GenericAPIView):
    '''购物车全选商品'''
    serializer_class = CartSelectAllSerializer

    def perform_authentication(self, request):
        '''重写父类APIView方法， 在进入视图前,不验证JWT '''
        pass

    def put(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        # 判断是否登陆
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 已登陆
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)

            # 获取购物车里的全部商品id
            sku_id_list = redis_cart.keys()
            if selected:
                # 全选
                redis_conn.sadd('cart_selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_conn.srem('cart_selected_%s' % user.id, *sku_id_list)

            return Response({'message':'OK'})
        else:
            # 未登陆
            cookie_cart_str = request.COOKIES.get('cart')
            # print(cart_str)
            if cookie_cart_str:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart_str.encode()))
            else:
                cart_dict ={}

                # cart_dict = {
                #     sku_id: {
                #         count: 10
                #         selected: True
                #     },
                #     sku_id: {
                #         count: 20
                #         selected: False
                #     }
                # }

            response = Response({'message':'OK'})

            # 如果购物车有商品
            if cart_dict:
                # 遍历购物车数据cart_dict字典中的值, 把值中的小字典的值selected都改成当前的全选或者取消全选相状态
                for count_selected_dict in cart_dict.values():
                    count_selected_dict['selected'] = selected
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('cart', cart_str, constants.CART_COOKIE_EXPIRES)

            return response