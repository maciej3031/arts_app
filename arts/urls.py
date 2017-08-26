# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'article', views.ArticleViewSet, base_name='article')
router.register(r'category', views.CategoryViewSet, base_name='category')

app_name = 'arts'  # to differentiate the URL names between apps (if there are more than one app)
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'detail/$', views.detail, name='detail'),
    url(r'advance/$', views.advance, name='advance'),
    url(r'poll/$', views.poll, name='poll'),
    url(r'^', include(router.urls)),
]
