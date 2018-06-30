from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from .utils import OAuthQQ # QQ登陆辅助工具类
from rest_framework.response import Response
from rest_framework import status
from .exceptions import OAuthQQAPIError
from .models import OAuthQQUser  # 导入openid与user_id关联的模型表
from .serializers import OAuthQQUserSerializer

# Create your views here.

# 第一步++++++++++++++++++++++++++++++++++++++++
class QQAuthUrlView(APIView):
    '''点击QQ登陆, 处理请求, 生成跳转页面的url'''

    def get(self,request):
        # 获取参数
        next = request.query_params.get('next')

        # 拼接url
        oauth_qq = OAuthQQ(state=next)
        # 封装的方法(通过QQ身份验证,QQ返回的必要数据)
        login_url = oauth_qq.get_qq_login_url()
        print(login_url)
        # https://graph.qq.com/oauth2.0/authorize?response_type=code&scope=get_user_info&state=%2F&client_id=101474184&redirect_uri=http%3A%2F%2Fwww.meiduo.site%3A8080%2Foauth_callback.html

        # 返回给前端去访问
        return Response({'login_url': login_url})


# 第二步++++++++++++++++++++++++++++++++++++++++++++
class QQAuthUserView(CreateAPIView):
    '''QQ登陆成功生成code, 通过code到QQ服务器获取登陆用户唯一表示openid'''

    '''保存页面使用序列化器'''
    # 校验比较多,使用序列化器
    serializer_class = OAuthQQUserSerializer

    def get(self,request):

        # 从前端url中获取code
        code = request.query_params.get('code')
        if not code:
            return Response({'message':'code不存在'},status=status.HTTP_400_BAD_REQUEST)

        oauth_qq = OAuthQQ()
        try:
            # 通过code获取QQ提供的access_token    # 封装方法
            access_token = oauth_qq.get_access_token(code)

            # 通过access_token获取openid          # 封装方法
            openid = oauth_qq.get_openid(access_token)
        except OAuthQQAPIError:
            return Response({'message':'访问QQ接口异常'},status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 通过openid在数据库OAuthQQUser中查询用户是否绑定过
        try:
            oauth_qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果未查到,证明未绑定,处理openid构造自己的access_token并返回
            # access_token 用户是第一次使用QQ登录时返回，其中包含openid，用于绑定身份使用，注意这个是我们自己生成的
            # 使用itsdangerous生成凭据access_token
            access_token = oauth_qq.genrate_bind_user_access_token(openid)
            return Response({'access_token': access_token})

        else:
            # 如果查询到,证明绑定或,签发JWT token
            # 手动创建JWT-token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            user = oauth_qq_user.user
            payload = jwt_payload_handler(user)  # 传入user模型对象中,这就是用户身份信息加入在token
            token = jwt_encode_handler(payload)
            # 返回数据
            return Response({
                'username':user.username,
                'user_id':user.id,
                'token':token
            })



    # 保存页面绑定用户
    # def post(self,request):
    #     '''保存页面绑定用户'''

        # 获取参数
        # 校验参数
        # 查询用户是否存在
        # 用户存在,校验密码,绑定openid
        # 用户不存在,创建用户,绑定openid




