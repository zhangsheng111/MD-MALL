from django.shortcuts import render
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView

# Create your views here.
from .serializers import ImageCodeCheckSerializer
import random
from meiduo_mall.libs.yuntongxun.sms import CCP
import logging
from rest_framework.response import Response
from rest_framework import status


logger = logging.getLogger('Django')


class ImageCodeView(APIView):
    '''图片验证码'''
    # 路径参数
    # 接收前端发来的图片验证码id
    def get(self,request,image_code_id):

        # 使用第三方生成验证码图片
        text, image = captcha.generate_captcha()

        # 把验证码存入redis
        redis_conn = get_redis_connection('verificate_code')
        redis_conn.setex('image_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 返回验证码图片(不需要REST framework框架的Response帮助我们决定返回响应数据的格式)
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(GenericAPIView):
    '''发送短信验证'''

    # 设置通用属性(序列化器)
    serializer_class = ImageCodeCheckSerializer

    # 接收前端的请求
    def get(self,request,mobile):
        # 反序列化验证数据
        serializer = self.get_serializer(data=request.query_params)
        # 如果序列化有问题就抛出异常
        serializer.is_valid(raise_exception=True)

        # 数据验证没问题,生成短信验证码

        sms_code = '%06d' % random.randint(0,999999)
        print(sms_code)

        # 保存验证码和发送状态 到redis服务器
        redis_conn = get_redis_connection('verificate_code')
        # redis_conn.setex('sms_code_%s' % constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % constants.SMS_CODE_REDIS_EXPIRES, 1)

        # redis的管道(收集操作,一次执行完,避免重复操作数据库,提高性能)
        pl = redis_conn.pipeline()
        pl.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()


        # 发送验证码给手机
        # 操作数据库等错误不需要try捕获
        # try:
        #     expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60) # 除以60,因为expires单位是分钟
        #     ccp = CCP()
        #     result = ccp.send_template_sms(mobile, [sms_code, expires], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
        #     # 因为返回是字符串数据,用rest_framework的返回可以自动根据浏览器的请求类型返回相同的类型数据,以便浏览器识别
        #     return Response({'message': '发送短信异常'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # else:
        #     if result == 0:
        #         logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        #         return Response({'message': '发送短信成功'}, status=status.HTTP_200_OK)
        #
        #     else:
        #         logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)
        #         return Response({'message': '发送短信失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #
        return Response({'message':'OK'},status=status.HTTP_200_OK)