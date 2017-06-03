# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from arts.WebPageParser import WebPageParserKW
from arts.models import do_db_operations

# Liczba dni wstecz, z których pobierane mają być artykuły
DAYS = 7

# liczba stron do przeiterowania dla danej kategorii
NUM_OF_PAGES = 30

# link do strony głównej
global_url = "http://kopalniawiedzy.pl"


class Command(BaseCommand):
    def handle(self, **options):
        try:
            soup = WebPageParserKW.get_soup_of_url(global_url)
        except AttributeError:
            print('Nie odnaleziono strony: {}'.format(global_url))
        else:
            article_url_list = WebPageParserKW.get_article_url_list(soup, global_url, NUM_OF_PAGES, DAYS)	
            for num, article_url in enumerate(article_url_list):
                try:
                    article_soup = WebPageParserKW.get_soup_of_url(article_url)
                except AttributeError:
                    print("Nie odnaleziono strony: {}".format(article_url))
                    continue
                try:
                    article_category_date_content_class = article_soup.find(class_="article-time-and-cat")
                    article_category = article_category_date_content_class.select('a')[0].text
                except IndexError:
                    print("Nie znaleziono kategorii na stronie: {}".format(article_url))
                    continue
                try:
                    do_db_operations(article_url, article_category, article_soup, global_url)
                except UnicodeEncodeError:
                    continue
