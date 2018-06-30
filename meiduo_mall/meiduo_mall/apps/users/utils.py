import re
from .models import User
from django.contrib.auth.backends import ModelBackend


def jwt_response_payload_handler(token, user=None, request=None):
    '''自定义jwt 登陆验证成功返回带有用户身份信息的token给浏览器'''
    '''需要在配置文件dev中配置JWT_AUTH'''

    print('token',token)
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }



def get_user_by_account(account):
    '''用手机号和用户名都获取到要查的user对象,再通过user对象去取出密码,然后验证'''
    try:
        if re.match(r'^1[3-9]\d{9}$',account):
            # 账号为手机号
            user = User.objects.get(mobile=account)
        else:
            # 账号为用户名
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None

    else:
        return user


# Dajngo的认证系统中提供的authenticate方法支持登录账号可以是用户名也可以是手机号
# 重写认证系统, 需要在配置文件中声明我们自己定义的方法

class UsernameMobileAuthBackend(ModelBackend):
    '''自定义用户名手机号认证'''
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        if user and user.check_password(password):
            return user




