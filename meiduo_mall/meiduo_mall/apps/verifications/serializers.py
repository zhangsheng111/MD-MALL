from rest_framework import serializers
from django_redis import get_redis_connection


'''创建序列化器'''
class ImageCodeCheckSerializer(serializers.Serializer):
    '''图片验证码校验序列器'''
    # 前端传过来的输入的验证码和网页发来的uuid进行校验
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4,min_length=4)

    # 多个值进行校验
    def validate(self, attrs):
        # attrs是字典(里面前端转过来的数据)
        print(attrs)

        # 获取值
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 获取redis中真实的验证码,和前端的进行比较
        redis_conn = get_redis_connection('verificate_code')
        redis_image_code_text = redis_conn.get('image_%s' % image_code_id)
        if not redis_image_code_text:
            raise serializers.ValidationError('图片验证码失效')

        # 删除redis中的图片验证,防止多次使用一个验证码
        # redis_conn.delete('image_%s' % image_code_id)


        redis_image_code_text = redis_image_code_text.decode()
        if redis_image_code_text.lower() != text.lower():
            raise serializers.ValidationError('图片验证码输入有误')

        # 判断本次是否已经发送短信验证码,如果已经发送在倒计时60秒内再发送会提示请求频繁
        mobile = self.context['view'].kwargs['mobile']
        if redis_conn.get('send_flag_%s' % mobile):
            raise serializers.ValidationError('请求操作过于频繁')

        return attrs




