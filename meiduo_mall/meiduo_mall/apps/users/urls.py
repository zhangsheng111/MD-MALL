from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token


urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.CheckUsernameViews.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.CheckMobileViews.as_view()),
    url(r'^users/$', views.RegisterView.as_view()),

    # 签发JWT的视图
    url(r'^authorizations/$', obtain_jwt_token)

]
# this.host + '/usernames/' + this.username + '/count/'