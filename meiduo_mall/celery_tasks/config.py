# 配置中间人broker,相当于任务仓库

broker_url = "redis://127.0.0.1/15"




# 启动celery: celery -A celery_tasks.main worker -l info