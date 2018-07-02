from django.conf.urls import url
from rest_framework import routers

from . import views
from rest_framework_jwt.views import obtain_jwt_token


urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.CheckUsernameViews.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.CheckMobileViews.as_view()),
    url(r'^users/$', views.RegisterView.as_view()),

    # Django REST framework JWT提供了登录签发JWT的视图，可以直接使用
    #==================================================
    #当购物车数据在登陆的同时自动合并时, 需要在视图中重写登陆验证
    #==================================================
    # url(r'^authorizations/$', obtain_jwt_token),# 购物车合并, 需要重写验证
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),

    # 获取用户中心数据
    url(r'^user/$', views.UserDetailView.as_view()),
    # 保存email
    url(r'^email/$', views.EmailView.as_view()),
    # 邮箱验证链接请求验证
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    # 保存历史浏览记录
    url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),

]

# 查询用户收货地址的路由
router = routers.DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name='addresses')

urlpatterns += router.urls


# this.host + '/usernames/' + this.username + '/count/'