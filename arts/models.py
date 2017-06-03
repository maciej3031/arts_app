# -*- coding: utf-8 -*-
import os
import urllib.error
import urllib.request

from django.contrib.contenttypes.fields import GenericRelation
from django.core.files import File
from django.db import models
from django.utils import timezone
from star_ratings.models import Rating

from .WebPageParser import DateTimeParser


class AdvanceSearch:
    site_id = None
    category_id = None
    author = None
    keywords = None
    date = None
    rate = None

    def __init__(self, site_id, category_id, author, keywords, date, rate):
        self.site_id = site_id
        self.category_id = category_id
        self.author = author
        self.keywords = keywords
        self.date = date
        self.rate = rate


class Category(models.Model):
    category_name = models.CharField("Nazwa kategorii", max_length=100)
    articles_number = models.IntegerField(default=0, editable=False)

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def get_articles_number(self):
        self.articles_number = Article.objects.filter(category_id=self).count()
        self.save()


class Site(models.Model):
    site_name = models.CharField("Treść", max_length=255)
    articles_number = models.IntegerField(default=0, editable=False)

    def __str__(self):
        return self.site_name

    class Meta:
        verbose_name = "Strona źródłowa"
        verbose_name_plural = "Strony źródłowe"

    def get_articles_number(self):
        self.articles_number = Article.objects.filter(site_id=self).count()
        self.save()


class Article(models.Model):
    title = models.CharField("Tytuł", max_length=255, unique=True)
    article_text = models.TextField("Treść")
    author = models.CharField("Autor", max_length=255, blank=True)
    pub_date = models.DateTimeField("Data dodania")
    image_url = models.URLField("Źródło obrazka", blank=True)
    image = models.ImageField("Zdjęcie", upload_to="kw/", blank=True, null=True)
    article_url = models.URLField("Źródło", unique=True)
    site_id = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Strona źródłowa")
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategoria")
    rate = GenericRelation(Rating, related_query_name='articles')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Artykuł"
        verbose_name_plural = "Artykuły"

    @classmethod
    def get_article_query_set(cls, adv_search):
        query_set = cls.objects.all()
        query_set = cls.get_article_query_set_by_site(query_set, adv_search)
        query_set = cls.get_article_query_set_by_category(query_set, adv_search)
        query_set = cls.get_article_query_set_by_author(query_set, adv_search)
        query_set = cls.get_article_query_set_by_keywords(query_set, adv_search)
        query_set = cls.get_article_query_set_by_date(query_set, adv_search)
        query_set = cls.get_article_query_set_by_rate(query_set, adv_search)
        return query_set

    @staticmethod
    def get_article_query_set_by_site(query_set, adv_search):
        if adv_search.site_id:
            query_set = query_set.filter(site_id=adv_search.site_id)
        return query_set

    @staticmethod
    def get_article_query_set_by_category(query_set, adv_search):
        if adv_search.category_id:
            query_set = query_set.filter(category_id=adv_search.category_id)
        return query_set

    @staticmethod
    def get_article_query_set_by_author(query_set, adv_search):
        if adv_search.author:
            for word in adv_search.author.split(" "):
                query_set = query_set.filter(author__icontains=word)
        return query_set

    @staticmethod
    def get_article_query_set_by_keywords(query_set, adv_search):
        if adv_search.keywords:
            for word in adv_search.keywords.split(" "):
                query_set = query_set.filter(article_text__icontains=word)
        return query_set

    @staticmethod
    def get_article_query_set_by_date(query_set, adv_search):
        if adv_search.date == "1_day":
            temp_date = timezone.now() - timezone.timedelta(days=1)
            query_set = query_set.filter(pub_date__gte=temp_date)
        elif adv_search.date == "1_week":
            temp_date = timezone.now() - timezone.timedelta(weeks=1)
            query_set = query_set.filter(pub_date__gte=temp_date)
        elif adv_search.date == "1_month":
            temp_date = timezone.now() - timezone.timedelta(weeks=4)
            query_set = query_set.filter(pub_date__gte=temp_date)
        elif adv_search.date == "3_month":
            temp_date = timezone.now() - timezone.timedelta(weeks=12)
            query_set = query_set.filter(pub_date__gte=temp_date)
        return query_set

    @staticmethod
    def get_article_query_set_by_rate(query_set, adv_search):
        rates = Rating.objects.all()
        if adv_search.rate.startswith("gte"):
            art_ids = rates.filter(average__gte=float(adv_search.rate[-1:])).values_list('object_id')
            query_set = query_set.filter(id__in=art_ids)
        elif adv_search.rate.startswith("lte"):
            art_ids = rates.filter(average__gt=0, average__lte=float(adv_search.rate[-1:])).values_list('object_id')
            query_set = query_set.filter(id__in=art_ids)
        return query_set

    def get_remote_title(self, article_soup):

        if self.article_url and not self.title:
            try:
                article_title = article_soup.select('h1')[0].text
            except IndexError:
                print("Nie znaleziono tytułu na stronie: {}".format(self.article_url))
            else:
                self.title = article_title

    def get_remote_article_text(self, article_soup):

        if self.article_url and not self.article_text:
            article_article_text_content_class = article_soup.find(class_="article-text text-small")
            try:
                article_article_text = "\n".join(
                    [article_text.text for article_text in article_article_text_content_class.find_all('p')[0:-3]]
                )
            except IndexError:
                print("Nie znaleziono tekstu artykulu na stronie: {}".format(self.article_url))
            else:
                self.article_text = article_article_text

    def get_remote_author(self, article_soup):

        if self.article_url and not self.author:
            article_author_content_class = article_soup.find(class_="author")
            try:
                article_author = article_author_content_class.select('strong')[0].text
            except IndexError:
                print("Nie znaleziono autora na stronie: {}".format(self.article_url))
                article_author = "Autor nieznany"
            self.author = article_author

    def get_remote_pub_date(self, article_soup):

        if self.article_url and not self.pub_date:
            article_category_date_content_class = article_soup.find(class_="article-time-and-cat")
            try:
                article_pub_date = article_category_date_content_class.select('time')[0].text
                article_pub_date = DateTimeParser.change_date_format(article_pub_date)
            except IndexError:
                print("Nie znaleziono daty na stronie: {}".format(self.article_url))
            else:
                self.pub_date = article_pub_date

    def get_remote_image_url(self, article_soup, global_url):

        if self.article_url and not self.image_url:
            article_image_content_class = article_soup.find(class_="first")
            if article_image_content_class:
                article_image_url = global_url + article_image_content_class.get('src')
            else:
                print("Nie znaleziono ilustracji na stronie: {}".format(self.article_url))
                article_image_url = ''  # wówczas wartość image_url zaplanowano na wartość pustą
            self.image_url = article_image_url

    def get_remote_image(self):

        if self.image_url and not self.image:
            try:
                result = urllib.request.urlretrieve(self.image_url)
            except urllib.error.URLError:
                pass
                print("Nie udalo sie pobrac ilustracji dla: {}".format(self.image_url))
            else:
                self.image.save(
                    os.path.basename(self.image_url),
                    File(open(result[0], 'rb'))
                )
                self.save()


class Question(models.Model):

    question_text = models.CharField("Pytanie",  max_length=255, blank=False)
    pub_date = models.DateTimeField("Data dodania")

    def __str__(self):
        return self.question_text

    class Meta:
        verbose_name = "Pytanie"
        verbose_name_plural = "Pytania"


class Choice(models.Model):

    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Pytanie", blank=False)
    choice_text = models.CharField("Odpowiedź",  max_length=100, blank=False)
    votes = models.IntegerField(default='0')

    def __str__(self):
        return self.choice_text

    class Meta:
        verbose_name = "Odpowiedź"
        verbose_name_plural = "Odpowiedzi"


class Opinion(models.Model):
    opinion_text = models.CharField("Opinia", max_length=255, blank=False)
    pub_date = models.DateTimeField("Data dodania")

    def __str__(self):
        return self.opinion_text

    class Meta:
        verbose_name = "Opinia"
        verbose_name_plural = "Opinie"


def do_db_operations(article_url, article_category, article_soup, site_url):
    category = Category.objects.filter(category_name=article_category).first()
    if not category:
        category = Category(category_name=article_category)
        category.save()

    site = Site.objects.filter(site_name=site_url).first()
    if not site:
        site = Site(site_name=site_url)
        site.save()

    article = Article.objects.filter(article_url=article_url).first()
    if article:
        article.get_remote_author(article_soup)
        article.get_remote_image_url(article_soup, site_url)
    else:
        article = Article(article_url=article_url, category_id=category, site_id=site)
        article.get_remote_title(article_soup)
        article.get_remote_article_text(article_soup)
        article.get_remote_author(article_soup)
        article.get_remote_pub_date(article_soup)
        article.get_remote_image_url(article_soup, site_url)

    article.save()
    article.get_remote_image()
    category.get_articles_number()
    site.get_articles_number()