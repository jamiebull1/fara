# -*- coding: utf-8 -*-
"""Model for the scraped FARA item.
"""
import scrapy


class FaraItem(scrapy.Item):
    """Item representing an Active Foreign Principal
    """
    url = scrapy.Field()
    country = scrapy.Field()
    state = scrapy.Field()
    reg_num = scrapy.Field()
    address = scrapy.Field()
    foreign_principal = scrapy.Field()
    date = scrapy.Field()
    registrant = scrapy.Field()
    exhibit_urls = scrapy.Field()
