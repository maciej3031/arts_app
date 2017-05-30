# -*- coding: utf-8 -*-
import os
import re
import urllib.error
import urllib.request

import bs4
import pytz
import requests
from django.core.files import File
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from star_ratings.models import Rating


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
        if adv_search.rate.startswith("gt"):
            art_ids = rates.filter(average__gte=float(adv_search.rate[-1:])).values_list('object_id')
            query_set = query_set.filter(id__in=art_ids)
        elif adv_search.rate.startswith("lt"):
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
                article_pub_date = WebPageParserKW.change_date_format(article_pub_date)
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


class WebPageParser:
    @staticmethod
    def get_ful_page(url):
        """Pobiera całą stronę, odkodowanie utf-8, sprawdzenie statusu, zwraca obiekt typu requests"""
        try:
            page = requests.get(url, timeout=60)
            page.encoding = 'utf-8'
            page.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
            page = ""
        return page

    @staticmethod
    def get_soup_of_url(next_page_url):

        article_list_page = WebPageParserKW.get_ful_page(next_page_url)
        article_list_soup = bs4.BeautifulSoup(article_list_page.text, 'lxml')
        return article_list_soup

    @staticmethod
    def get_list_of_tag_from_list(tag, soup_list):

        result_list = [content.find_all(tag) for content in soup_list]
        return result_list

    @staticmethod
    def get_list_of_tag_and_css_cls_from_list(tag, css_cls, soup_list):

        result_list = [content.find_all(tag, attrs={'class': css_cls}) for content in soup_list]
        return result_list


class WebPageParserKW(WebPageParser):
    @staticmethod
    def _match_last_hours(date_time):

        current_date = timezone.datetime.now()
        pattern = r"\b([0-9]+ godz. temu)\b"
        if re.match(pattern, date_time):
            new_date = "{:02}/{:02}/{:02}".format(current_date.day, current_date.month, current_date.year) + " " + \
                       "{:02}:{:02}".format(current_date.hour - int(date_time[0]), current_date.minute)
            return new_date
        else:
            return False

    @staticmethod
    def _match_last_minutes(date_time):

        current_date = timezone.datetime.now()
        pattern = r"\b([0-9]+ min. temu)\b"
        if re.match(pattern, date_time):
            new_date = "{:02}/{:02}/{:02}".format(current_date.day, current_date.month, current_date.year) + " " + \
                       "{:02}:{:02}".format(current_date.hour, current_date.minute)
            return new_date
        else:
            return False

    @staticmethod
    def _match_article_date(date_time, months):

        try:
            date_time = date_time.split(", ")
            date_time = [i.split(" ") for i in date_time]
            new_date = []
            for elem in date_time[0]:
                if elem in months.keys():
                    elem = months[elem]
                new_date.append(elem)

            new_date = "".join(new_date) + " " + date_time[1][0]
        except IndexError:
            new_date = None

        return new_date

    @staticmethod
    def _convert_to_timezone_object(new_date):

        new_date = timezone.datetime.strptime(new_date, "%d/%m/%Y %H:%M")
        new_date = pytz.timezone(timezone.get_default_timezone_name()).localize(new_date)
        return new_date

    @staticmethod
    def change_date_format(date_time):
        """Zmienia format daty, ze stringa: 1 stycznia 2017, 12:12 na obiekt timezone"""

        try:
            assert type(date_time) is str
        except AssertionError:
            new_date = None
            print("Podana wartość daty nie jest stringiem")
        else:
            current_date = timezone.datetime.now()
            months = {"stycznia": "/01/", "lutego": "/02/", "marca": "/03/", "kwietnia": "/04/", "maja": "/05/",
                      "czerwca": "/06/", "lipca": "/07/", "sierpnia": "/08/", "września": "/09/",
                      "października": "/10/",
                      "listopada": "/11/", "grudnia": "/12/",
                      "wczoraj": "{:02}/{:02}/{:02}".format(current_date.day - 1, current_date.month,
                                                            current_date.year),
                      "dzisiaj": "{:02}/{:02}/{:02}".format(current_date.day, current_date.month, current_date.year),
                      "1": "01", "2": "02", "3": "03", "4": "04", "5": "05", "6": "06", "7": "07", "8": "08", "9": "09"}

            if WebPageParserKW._match_last_hours(date_time):
                new_date = WebPageParserKW._match_last_hours(date_time)
            elif WebPageParserKW._match_last_hours(date_time):
                new_date = WebPageParserKW._match_last_minutes(date_time)
            else:
                new_date = WebPageParserKW._match_article_date(date_time, months)

        if new_date is not None:
            new_date = WebPageParserKW._convert_to_timezone_object(new_date)
        return new_date

    @staticmethod
    def get_article_url_list(soup, global_url, num_of_pages, num_of_days):
        """Zwraca listę wszystki url artykułów biorąc obiekt typu beautiful soup"""

        try:
            category_pages_urls = WebPageParserKW.get_categories_urls(global_url, soup)
        except IndexError:
            print("Nie odnaleziono tagu o klasie = 'bottom-bar'")
        else:
            article_url_list = []

            for category_url in category_pages_urls:
                iterator = 0  # odpowiada za liczbę sprawdzonych podstron kategorii
                next_page_url = category_url

                # pobieramy linki do artykułów z kolejnych podstron
                while iterator < num_of_pages:
                    try:
                        article_list_soup = WebPageParserKW.get_soup_of_url(next_page_url)
                    except AttributeError:
                        print("Nie odnaleziono strony: {}".format(next_page_url))	
                        continue
                    try:
                        article_url_list_per_cat = WebPageParserKW.get_article_url_list_per_category(
                            next_page_url, num_of_days, global_url, article_list_soup)
                    except Exception:
                        print("Blad przy pobieraniu linkow i dat ze strony: {}".format(next_page_url))
                        continue
                    else:
                        article_url_list.extend(article_url_list_per_cat)
                    try:
                        next_page_url = WebPageParserKW.get_next_page_url(article_list_soup, global_url)
                        iterator += 1
                    except IndexError:
                        print("Nie znaleziono przycisku nastepnej strony dla kategorii: {}".format(category_url))
                        break
            return article_url_list

    @staticmethod
    def get_categories_urls(global_url, soup):

        categories_list = soup.find_all(class_="bottom-bar")[0]
        categories_list_a = categories_list.find_all("a")
        category_pages_urls = ["".join([global_url, a.get('href')]) for a in categories_list_a]
        return category_pages_urls

    @staticmethod
    def get_urls_from_a_tag(global_url, article_list_content_a):

        urls = [global_url + content_a[0].get('href') for content_a in article_list_content_a]
        return urls

    @staticmethod
    def get_dates_from_span_tag(article_list_content_span):

        dates = [content_span[0].text for content_span in article_list_content_span]
        return dates

    @staticmethod
    def get_article_url_list_per_category(next_page_url, num_of_days, global_url, article_list_soup):

        article_list_content_class = article_list_soup.find_all(class_="article-list-content article-list-fixed")

        list_all_a_tags_per_cat = WebPageParserKW.get_list_of_tag_and_css_cls_from_list("a", "title", article_list_content_class)
        list_all_span_tags_per_cat = WebPageParserKW.get_list_of_tag_from_list("span", article_list_content_class)

        list_of_all_urls_per_cat_page = WebPageParserKW.get_urls_from_a_tag(global_url, list_all_a_tags_per_cat)
        list_of_all_dates_per_cat_page = WebPageParserKW.get_dates_from_span_tag(list_all_span_tags_per_cat)

        article_url_list_per_cat = WebPageParserKW.get_article_urls_by_date(
            num_of_days, next_page_url, list_of_all_dates_per_cat_page, list_of_all_urls_per_cat_page)

        return article_url_list_per_cat

    @staticmethod
    def get_article_urls_by_date(num_of_days, next_page_url, list_of_dates, list_of_urls):

        article_url_list_per_cat = []
        for num, date in enumerate(list_of_dates):
            current_date = timezone.now()

            new_article_date = WebPageParserKW.change_date_format(date)
            if new_article_date is None:
                print("Nie znaleziono daty na stronie: {}".format(next_page_url))
                continue

            if current_date - new_article_date < timezone.timedelta(days=num_of_days):
                article_url_list_per_cat.append(list_of_urls[num])
        return article_url_list_per_cat

    @staticmethod
    def get_next_page_url(article_list_soup, global_url):

        next_page = article_list_soup.find_all(class_="next")[0]
        next_page_url = global_url + next_page.get('href')
        return next_page_url

    @staticmethod
    def do_db_operations(article_url, article_site, article_category, article_soup, global_url):

        category = Category.objects.filter(category_name=article_category).first()
        if not category:
            category = Category(category_name=article_category)
            category.save()

        site = Site.objects.filter(site_name=article_site).first()
        if not site:
            site = Site(site_name=article_site)
            site.save()

        article = Article.objects.filter(article_url=article_url).first()
        if article:
            article.get_remote_author(article_soup)
            article.get_remote_image_url(article_soup, global_url)
        else:
            article = Article(article_url=article_url, category_id=category, site_id=site)
            article.get_remote_title(article_soup)
            article.get_remote_article_text(article_soup)
            article.get_remote_author(article_soup)
            article.get_remote_pub_date(article_soup)
            article.get_remote_image_url(article_soup, global_url)

        article.save()
        article.get_remote_image()
        category.get_articles_number()
        site.get_articles_number()
