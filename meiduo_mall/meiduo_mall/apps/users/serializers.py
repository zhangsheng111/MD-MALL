from rest_framework import serializers
from .models import User
import re
from django_redis import get_redis_connection

# 手动签发JWT,手动创建token
from rest_framework_jwt.settings import api_settings

class CreateUserSerializer(serializers.ModelSerializer):
    '''创建用户序列化'''

    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)  # write_only=True代表不需要返回前端,只在后端验证等
    # token载体,用于保存浏览器端根据浏览器发来的请求信息(用户名密码)加盐(secret)再加密后的字符串,在浏览器请求后返回给浏览器,以便下次访问服务器验证身份.
    token = serializers.CharField(label='登陆状态token', read_only=True) # read_only=True代表需要返回前端字段

    class Meta:
        model = User
        # 进行序列化和反序列化的字段
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow','token')
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }


    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value


    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value


    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verificate_code')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_code_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data


    # 创建用户
    def create(self,validated_data):
        '''删除数据模型中不存在的字段'''
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        # 调用父类的create方法添加模型对象
        user = super(CreateUserSerializer, self).create(validated_data)
        # 密码加密
        user.set_password(validated_data['password'])
        # 创建模型对象
        user.save()

        # 手动创建JWT-token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)  # 传入user模型对象中,这就是用户身份信息加入在token
        token = jwt_encode_handler(payload)
        # 给user的字段赋值,再序列化成json数据,返回给浏览器
        user.token = token

        return user


