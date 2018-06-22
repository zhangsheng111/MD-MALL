from celery import Celery


# 为celery使用django配置文件进行设置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建celery应用
celery_app = Celery('meiduo')     # 起名区分celery

# 导入中间人broker
celery_app.config_from_object('celery_tasks.config')   # config模块也是对象

# 加入任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])  # 列表存放可以存放多个不同任务,自动找到tasks模块
