from rest_framework import serializers

from .models import Article, Category


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ('id', 'title', 'article_text', 'author', 'pub_date', 'image_url', 'article_url', 'site_id',
                  'category_id')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'category_name', 'articles_number')
