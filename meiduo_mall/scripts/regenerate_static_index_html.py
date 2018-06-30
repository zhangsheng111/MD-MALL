# 配置django环境

import sys
# 加入包的搜索路径
sys.path.insert(0, '../') # 把项目meiduo_mall目录添加进来, 以便找到ｄｊａｎｇｏ的配置文件ｄｅｖ
# print(sys.path)

import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    # 表示能够使用django里的配置文件
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

import django
# 让django初始化一次配置环境
django.setup()

from contents.crons import generate_static_index_html

if __name__ == '__main__':
    # 生成静态化的网页文件
    generate_static_index_html()



# 在scripts路径下运行python regenerate_static_index_html.py, 生成静态化文件