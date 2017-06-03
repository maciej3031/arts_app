# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import pytz

from .models import Article, Category, Site, Rating


class TestPages(TestCase):
    def setUp(self):
        Category.objects.create(id=1, category_name="Medycyna", articles_number=1)
        Site.objects.create(id=1, site_name="http://kopalniawiedzy.pl", articles_number=1)
        Article.objects.create(
            id=1,
            title="Tytuł1",
            article_text="Treść tekst1tekst",
            author="Autor{}".format(1),
            pub_date=timezone.now() - timezone.timedelta(hours=15),
            article_url="http://kopalniawiedzy.pl.example1",
            site_id=Site.objects.filter(site_name="http://kopalniawiedzy.pl").first(),
            category_id=Category.objects.filter(id=1).first(),
        )
        Rating.objects.create(count=1, total=1, average=5,
                              object_id=1)
        article = Article.objects.filter(title="Tytuł1").first()
        article.rate = Rating.objects.filter(object_id=article.id)
        article.save()

    def test_index_page(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_detail_page(self):
        client = Client()
        response = client.get(reverse('arts:detail'))
        self.assertEqual(response.status_code, 200)

    def test_advance_page(self):
        client = Client()
        response = client.get(reverse('arts:advance'))
        self.assertEqual(response.status_code, 200)

    def test_poll_page(self):
        client = Client()
        response = client.get(reverse('arts:poll'))
        self.assertEqual(response.status_code, 200)


class TestAdvanceSearch(TestCase):
    def setUp(self):
        categories = ["Medycyna", "Technologia", "Psychologia"]
        for i, cat in enumerate(categories):
            Category.objects.create(id=i+1, category_name=cat, articles_number=1)
        Site.objects.create(id=1, site_name="http://kopalniawiedzy.pl", articles_number=3)
        for i in range(1, 4):
            Article.objects.create(
                id=i,
                title="Tytuł{}".format(i),
                article_text="Treść tekst{}tekst".format(i),
                author="Autor{}".format(i),
                pub_date=timezone.now() - timezone.timedelta(hours=15*i),
                article_url="http://kopalniawiedzy.pl.example{}".format(i),
                site_id=Site.objects.filter(site_name="http://kopalniawiedzy.pl").first(),
                category_id=Category.objects.filter(id=i).first(),
            )
            Rating.objects.create(count=i, total=i, average=i,
                                  object_id=i)
            article = Article.objects.filter(title="Tytuł{}".format(i)).first()
            article.rate = Rating.objects.filter(object_id=article.id)
            article.save()

    def test_advance_random_search_specific_site(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': 1, 'category': '', 'author': '', 'keywords': '', 'date': '', 'rate': ''})
        self.assertContains(response, 'http://kopalniawiedzy.pl')

    def test_advance_random_search_specific_category(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '2', 'author': '', 'keywords': '', 'date': '', 'rate': ''})
        self.assertContains(response, 'Technologia')

    def test_advance_random_search_specific_author(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': 'Autor2', 'keywords': '', 'date': '', 'rate': ''})
        self.assertContains(response, 'Autor2')

    def test_advance_random_search_specific_keywords1(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': 'tekst2tekst', 'date': '', 'rate': ''})
        self.assertContains(response, 'tekst2tekst')

    def test_advance_random_search_specific_keywords2(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': 'tekst 3tekst', 'date': '', 'rate': ''})
        self.assertContains(response, 'tekst')
        self.assertContains(response, '3tekst')

    def test_advance_random_search_specific_keywords3(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': 'Treść tekst 1tekst', 'date': '', 'rate': ''})
        self.assertContains(response, 'tekst')
        self.assertContains(response, '1tekst')
        self.assertContains(response, 'Treść')

    def test_advance_random_search_specific_date(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': '', 'date': '1_day', 'rate': ''})
        self.assertContains(response, 'Tytuł1')

    def test_advance_random_search_specific_rate_gte3(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': '', 'date': '', 'rate': 'gte3'})
        self.assertContains(response, 'Tytuł3')

    def test_advance_random_search_specific_rate_lte1(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': '', 'date': '', 'rate': 'lte1'})
        self.assertContains(response, 'Tytuł1')

    def test_advance_random_search_no_such_article(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '3', 'category': '5', 'author': 'some author', 'keywords': 'something', 'date': '1_month', 'rate': 'gte4'})
        self.assertContains(response, "Nie znaleziono artykułu o podanych kryteriach")

    def test_advance_random_search_no_criteria(self):
        client = Client()
        response = client.post(reverse('arts:advance'),
                               {'site': '', 'category': '', 'author': '', 'keywords': '', 'date': '', 'rate': ''})
        self.assertContains(response, "Treść")





