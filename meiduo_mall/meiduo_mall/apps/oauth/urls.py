from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token


urlpatterns = [
    url(r'^qq/authorization/$',views.QQAuthUrlView.as_view()),
    url(r'^qq/user/$', views.QQAuthUserView.as_view())
]
