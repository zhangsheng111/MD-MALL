from django.shortcuts import render
from rest_framework.views import APIView
from .models import User
from rest_framework.response import Response


# Create your views here.

class CheckUsernameViews(APIView):
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
    '''校验用户名是否存在'''
    def get(self,request, mobile):

        # 从数据库读取该用户数量
        count = User.objects.filter(mobile=mobile).count()

        # 结果返回给前端
        data = {
            'mobile':mobile,
            'count': count
        }

        return Response(data)

from rest_framework.generics import CreateAPIView
from .serializers import CreateUserSerializer

class RegisterView(CreateAPIView):
        '''用户注册'''
        '''username, password, password2, sms_code, mobile, allow'''

        serializer_class = CreateUserSerializer

        # 接受参数
        # 校验参数
        # 获取短信验证码进行比较
        # 保存用户名数据
        # 返回结果
