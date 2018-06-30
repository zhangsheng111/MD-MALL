from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from django.conf import settings
import json
import logging
from .exceptions import OAuthQQAPIError

from . import constants

logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    QQ认证辅助工具类,用于连接QQ互联登陆
    """
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id or settings.QQ_CLIENT_ID       # 注册好的aapid
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI # 回调网址,就是QQ授权成功后的下一步的保存信息页面
        self.state = state or settings.QQ_STATE  # 用于保存登录成功后的跳转页面路径

    def get_qq_login_url(self):
        """
        点击QQ登陆,获取qq登录的网址
        :return: url网址
        """
        # url中必传的参数
        params = {
            'response_type': 'code',   # 指定请求QQ登陆后,QQ返回来的是code数据
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info',
        }
        # QQ文档
        url = 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(params)
        return url



    def get_access_token(self,code):
        '''通过code获取access_token'''

        # 准备url,向QQ请求access_token
        url = 'https://graph.qq.com/oauth2.0/token?'  # QQ文档
        print('1',url)
        # url中必传参数
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        # 拼接
        url = url + urlencode(params)
        print(url)

        try:
            # 发送请求,返回access_token
            resp = urlopen(url)

            resp_data = resp.read()  # urlopen提供的read方法
            resp_str = resp_data.decode()
            #  access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14

            # 解析(字符串解析成字典)
            resp_dict = parse_qs(resp_str)

        except Exception as e:
            logger.error('请求qq access_token异常')
            raise OAuthQQAPIError
        else:
            access_token = resp_dict.get('access_token',None)
            # print(access_token,type(access_token))

            return access_token[0]


    def get_openid(self,access_token):
        '''通过access_token获取openid'''

        # 准备url,向QQ服务器请求openid
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        # print(url)

        try:
            # 发送请求,返回openid
            resp = urlopen(url)

            resp_data = resp.read()  # urlopen提供的read方法
            resp_str = resp_data.decode()

            # 返回结果如下例:
            # callback( {"client_id": "YOUR_APPID", "openid": "YOUR_OPENID"} )\n;
            # 字符串截取
            resp_str = resp_str[10:-4]
            # json转成字典
            resp_dict = json.loads(resp_str)

        except Exception as e:
            logger.error('请求qq openid异常')
            raise OAuthQQAPIError
        else:
            openid = resp_dict.get('openid')
            return openid


    def genrate_bind_user_access_token(self,openid):
        '''用户第一次QQ登陆,生成包含用户opneid的access_token'''

        # 创建对象(第一参数是秘钥(盐), 第二个是设置绑定用户的access_token的有效期)
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        # 转换数据
        token = serializer.dumps({'openid': openid})

        return token.decode()

    @staticmethod
    def check_save_user_token(access_token):
        '''校验token'''
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)

        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data['openid']

