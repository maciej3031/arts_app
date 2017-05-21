from django.contrib import admin
from .models import *


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name', 'articles_number')


class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'site_name', 'articles_number')


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'pub_date', 'image', 'article_url', 'category_id')


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text', 'pub_date')


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'choice_text', 'votes')


class OpinionAdmin(admin.ModelAdmin):
    list_display = ('id', 'opinion_text', 'pub_date')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Site, SiteAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Opinion, OpinionAdmin)
