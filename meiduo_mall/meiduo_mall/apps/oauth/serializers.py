from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from oauth.utils import OAuthQQ
from users.models import User
from .models import OAuthQQUser

class OAuthQQUserSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(label='短信验证码',write_only=True)  # 传入时使用
    access_token = serializers.CharField(label='操作凭证',write_only=True) # 传入时使用
    token = serializers.CharField(read_only=True)  # 返回时使用
    # 因为模型中手机号是唯一的,这里需要去掉手机号的自动校验, 保证手机号已经存在也可以继续往下处理
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = User
        fields = ('mobile', 'password', 'sms_code', 'access_token','id','username','token')
        # 额外声明
        extra_kwargs = {
            'username': {
                'read_only': True
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

    def validate(self, attrs):

        # 检验access_token
        access_token = attrs['access_token']
        openid = OAuthQQ.check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')

        # 先存储在attrs中
        attrs['openid'] = openid

        # 检验短信验证码
        mobile = attrs['mobile']
        sms_code = attrs['sms_code']
        redis_conn = get_redis_connection('verificate_code')
        real_sms_code = redis_conn.get('sms_code_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果用户存在，检查用户密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = attrs['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
        return attrs


    def create(self, validated_data):
        openid = validated_data.get('openid')
        user = validated_data.get('user')
        mobile = validated_data['mobile']
        password = validated_data['password']
        # 查询用户是否存在

        if not user:
            # 用户不存在,创建用户,绑定openid
             # 直接创建并加密密码
            user = User.objects.create_user(username=mobile,mobile=mobile,password=password)

        # 用户存在,校验密码,绑定openid
        OAuthQQUser.objects.create(openid=openid, user=user)

        # 签发JWT
        # 手动创建JWT-token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)  # 传入user模型对象中,这就是用户身份信息加入在token
        token = jwt_encode_handler(payload)
        # 把token添加到user中返回给浏览器保存
        user.token = token

        return user

