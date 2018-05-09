from django.conf.urls import url

from . import views
from django.contrib import admin

urlpatterns = [
    url(r'admin', admin.site.urls),
    url(r'^$', views.index, name='index'),
    url(r'register', views.register, name='register'),
    url(r'signin', views.signin, name='signin'),
    url(r'signout', views.signout, name='signout'),
    url(r'upload', views.upload, name='upload'),
    url(r'subscribe', views.subscribe, name='subscribe'),
]
