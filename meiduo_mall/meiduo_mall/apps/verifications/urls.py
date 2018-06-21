from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^image_codes/(?P<image_code_id>[\w-]+)/$',views.ImageCodeView.as_view()),
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$',views.SMSCodeView.as_view())
]
# http://api.meiduo.site:8000/sms_codes/17631339300
# /?text=sdds&image_code_id=152897d7-0cb5-4976-8352-218ec57d2fae 404 (Not Found)
