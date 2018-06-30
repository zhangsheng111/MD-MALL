from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import User
from rest_framework.response import Response
from goods.models import SKU

# Create your views here.
# ==================================================================
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from .serializers import CreateUserSerializer, UserDetailSerializer,EmailSerializer,AddUserBrowsingHistorySerializer, SKUSerializer

# 创建数据库新数据 CreateAPIView
class RegisterView(CreateAPIView):
        '''用户注册视图'''
        '''username, password, password2, sms_code, mobile, allow'''

        serializer_class = CreateUserSerializer

        # 接受参数
        # 校验参数
        # 获取短信验证码进行比较
        # 保存用户名数据
        # 返回结果


class CheckUsernameViews(APIView):
    '''用户登陆校验'''
    '''校验用户名是否存在'''
    def get(self,request, username):

        # 从数据库读取该用户数量
        count = User.objects.filter(username=username).count()

        # 结果返回给前端
        data = {
            'username':username,
            'count': count
        }

        return Response(data)


class CheckMobileViews(APIView):
    '''用户登陆校验'''
    '''校验手机号是否存在'''
    def get(self,request, mobile):

        # 从数据库读取该用户数量
        count = User.objects.filter(mobile=mobile).count()

        # 结果返回给前端
        data = {
            'mobile':mobile,
            'count': count
        }

        return Response(data)


# ====================================================================
from rest_framework.permissions import IsAuthenticated

# 获取数据库中的数据 RetrieveAPIView
class UserDetailView(RetrieveAPIView):
    '''返回用户中心数据'''

    serializer_class = UserDetailSerializer
    # 指明只有登录的用户才能进入视图获取到数据
    permission_classes = [IsAuthenticated]


    def get_object(self):
        # 类视图中,可以使用request获取本次的请求对象
        # request对象中包含的属性user, 是本次请求的登陆用户模型类对象
        return self.request.user

# ========================================================================

# 更新数据库邮箱数据, UpdtaeAPIView
class EmailView(UpdateAPIView):
    '''保存更新用户的邮箱'''

    # 保存邮箱到数据库
    serializer_class = EmailSerializer
    # 必须是用户登陆状态
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # 类视图中,可以使用request获取本次的请求对象
        # request对象中包含的属性user, 是本次请求的登陆用户模型类对象
        return self.request.user

    # 接收邮箱
    # 校验邮箱
    # 查询该用户是否存在
    # 把邮箱保存到数据库
    # 序列化返回


class VerifyEmailView(APIView):
    '''用户点击验证链接后,校验token,更改邮箱的验证状态'''
    def get(self,request):
        # 从链接中获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)

        # 验证token
        user = User.check_verify_email_token(token)
        print('user', user)
        if user is None:
            return Response({'message':'链接信息失效'},status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({'message':'OK'})

# 对用户地址的增删改查以及设置默认地址\修改地址标题
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from . import serializers,constants

class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):

    serializer_class = serializers.UserAddressSerializer
    # 在用户登陆状态下
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 获取当前用户的所有地址信息的查询集
        return self.request.user.addresses.filter(is_deleted=False)

    # 查询用户地址信息
    def list(self,request,*args,**kwargs):
        queryset = self.get_queryset()
        # 把列表视图的该用户的所有地址信息的查询集序列化成json数据
        serializer = self.get_serializer(queryset,many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data
        })

    # 修改保存用户地址信息
    def create(self, request, *args, **kwargs):
        # 获取用户的地址数量
        count = self.request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数量已达上限'},status=status.HTTP_400_BAD_REQUEST)
        return super().create(request,*args,**kwargs)

    # 逻辑删除地址
    def destroy(self,request,*args,**kwargs):
        address = self.get_object()
        address.is_deleted = True
        address.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # 设置地址默认标题
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # 修改地址标题
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



# 用户浏览商品,保存历史记录到redis
class UserBrowsingHistoryView(CreateModelMixin, GenericAPIView):
    '''保存用户历史浏览记录'''
    serializer_class = AddUserBrowsingHistorySerializer
    # 用户必须是登陆状态才能访问该视图
    permission_classes = [IsAuthenticated]

    def post(self, request):
        '''保存历史记录'''
        return self.create(request)

    def get(self, request):
        """
        获取历史记录
        """
        user_id = request.user.id

        redis_conn = get_redis_connection("history")
        history = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        skus = []
        # 为了保持查询出的顺序与用户的浏览历史保存顺序一致
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        serializer = SKUSerializer(skus, many=True)
        return Response(serializer.data)