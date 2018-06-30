from rest_framework import serializers
from .models import User
import re
from django_redis import get_redis_connection
from . import constants
from goods.models import SKU


# 手动签发JWT,手动创建token
from rest_framework_jwt.settings import api_settings

class CreateUserSerializer(serializers.ModelSerializer):
    '''注册用户的序列化'''

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


# 创建返回给用户中心的数据的序列化器
class UserDetailSerializer(serializers.ModelSerializer):
    '''显示用户中心数据序列化器'''
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')



# 导入邮件发送功能
from celery_tasks.email.tasks import send_active_email

class EmailSerializer(serializers.ModelSerializer):
    '''验证邮箱的序列化器'''
    class Meta:
        model = User
        fields = ('id','email')
        extra_kwargs = {
            'email':{
                'required':True   # 反序列化时必须给email传值
            }
        }


    def update(self, instance, validated_data):

        # instance 视图中传来的user对象
        # validated_data  上面验证ok的数据
        email = validated_data.get('email')
        # 保存邮箱到数据库

        instance.email = email
        instance.save()

        # 生成邮件激活链接地址
        verify_url = instance.generate_verify_email_url()

        # 异步发送邮件
        send_active_email.delay(email, verify_url)

        return instance

#


# 创建收货地址的序列化器
from .models import Address

class UserAddressSerializer(serializers.ModelSerializer):

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    # 声明
    class Meta:
        model = Address
        exclude = ('is_deleted', 'user', 'update_time', 'create_time')

    def validate_mobile(self,value):
        '''验证手机号'''
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        '''重写create方法'''
        # 当前操作的用户对象也需要添加到地址表,以指明该地址属于当前的用户, 在创建新的地址数据表时, 需要在validated_data中添加用户对象的属性
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    '''地址标题的序列化器'''
    class Meta:
        model = Address
        fields = ('title',)





# 浏览历史记录序列化器
class AddUserBrowsingHistorySerializer(serializers.Serializer):
    '''序列化器'''
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)


    def validate_sku_id(self, value):
        """
        检验sku_id是否存在
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')
        return value

    def create(self, validated_data):
        """
        保存
        """
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        redis_conn = get_redis_connection("history")
        pl = redis_conn.pipeline()

        # 移除已经存在的本商品浏览记录
        pl.lrem("history_%s" % user_id, 0, sku_id)
        # 添加新的浏览记录
        pl.lpush("history_%s" % user_id, sku_id)   # history_6  表示是id为６的用户的浏览记录
        # 只保存最多5条记录
        pl.ltrim("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)

        pl.execute()

        return validated_data


class SKUSerializer(serializers.ModelSerializer):
    """
    查询历史记录对应的SKU序列化器
    """
    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')
