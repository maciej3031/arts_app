# -*- coding: utf-8 -*-
import re

import bs4
import pytz
import requests
from django.utils import timezone


class DateTimeParser:
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

            if DateTimeParser._match_last_hours(date_time):
                new_date = DateTimeParser._match_last_hours(date_time)
            elif DateTimeParser._match_last_hours(date_time):
                new_date = DateTimeParser._match_last_minutes(date_time)
            else:
                new_date = DateTimeParser._match_article_date(date_time, months)

        if new_date is not None:
            new_date = DateTimeParser._convert_to_timezone_object(new_date)
        return new_date


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

            new_article_date = DateTimeParser.change_date_format(date)
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


