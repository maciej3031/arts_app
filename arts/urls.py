# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

app_name = 'arts'      # to differentiate the URL names between apps (if there are more than one app)
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'detail/$', views.detail, name='detail'),
    url(r'advance/$', views.advance, name='advance'),
    url(r'poll/$', views.poll, name='poll'),
    url(r'article/$', views.article_list, name='article_list'),
    url(r'article/(?P<pk>[0-9]+)/$', views.article_detail, name='article_detail'),
    url(r'category/$', views.category_list, name='category_list'),
    url(r'category/(?P<pk>[0-9]+)/$', views.category_detail, name='category_detail'),
]