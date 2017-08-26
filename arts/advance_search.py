# -*- coding: utf-8 -*-


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