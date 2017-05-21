from django.conf.urls import url
from . import views

app_name = 'arts'      # to differentiate the URL names between apps (if there are more than one app)
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'detail/$', views.detail, name='detail'),
    url(r'advance/$', views.advance, name='advance'),
    url(r'poll/$', views.poll, name='poll'),
]