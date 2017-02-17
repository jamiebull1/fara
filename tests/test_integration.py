# -*- coding: utf-8 -*-
"""Integration test for the FARA spider.
"""
import json
import os
from pprint import pprint

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from fara.items import FaraItem
from fara.spiders.faraspider import FaraSpider


class TestIntegrationAgainstCache(object):
    """Integration test to run against cached pages (if present).

    This runs for the number of items listed in NUM_RESPONSES below. If
    they are already cached then the cache is used, otherwise they will be
    queried from the site and add them to the cache.
    """

    TEST_FEED_URI = "fara.test.json"

    def setup(self):
        """Make sure we don't have an old fara.test.json still stored.
        """
        try:
            os.remove(self.TEST_FEED_URI)
        except OSError:
            pass
        self.settings = get_project_settings()
        self.settings.update({
            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_IGNORE_HTTP_CODES': [302],
            'HTTPCACHE_DIR': 'httptestcache',
            'FEED_URI': self.TEST_FEED_URI,
            'NUM_RESPONSES': '2',
            })
        process = CrawlerProcess(self.settings)
        process.crawl(FaraSpider)
        process.start()
        with open(self.TEST_FEED_URI, 'r') as f_json:
            self.items = f_json.readlines()

    def teardown(self):
        """Remove fara.test.json when we're done.
        """
        os.remove(self.TEST_FEED_URI)

    def test_scraped_items(self):
        """Check that each item has the expected keys set.
        Fails if the returned json items don't contain the expected fields.
        """
        for item in self.items:
            item = json.loads(item)
            assert set(item.keys()) == set(FaraItem.fields.keys())

        """Check we set and received the right number of responses.
        Fails if the number is different to that in settings. Also fails if
        that number is not set to 2.
        """
        assert len(self.items) == int(self.settings.get('NUM_RESPONSES'))
        assert len(self.items) == 2

        """Check that our returned items load as we expect them to.
        Fails if the saved items are different to the stored ones below.
        """
        expected = [
            {u'address': u'8105 Ainsworth Avenue\r\nSpringfield\xa0\xa022152',
             u'country': u'AFGHANISTAN',
             u'date': u'2014-07-03 00:00:00',
             u'exhibit_urls': [
                {u'date': u'2014-07-03 00:00:00',
                 u'exhibit_url': u'http://www.fara.gov/docs/6065-Exhibit-AB-20140703-5.pdf',
                 u'foreign_principal': u'Transformatin and Continuity'}],
             u'foreign_principal': u'Transformation and Continuity',
             u'reg_num': u'6065',
             u'registrant': u'Roberti + White, LLC',
             u'state': u'VA',
             u'url': u'https://efile.fara.gov/pls/apex/f?p=171:200:0::NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:6065,Exhibit%20AB,AFGHANISTAN'},
            {u'address': u'House #3 MRRD Road\r\nDarul Aman\r\nKabul',
             u'country': u'AFGHANISTAN',
             u'date': u'2014-05-05 00:00:00',
             u'exhibit_urls': [
                {u'date': u'2014-05-05 00:00:00',
                 u'exhibit_url': u'http://www.fara.gov/docs/5945-Exhibit-AB-20140505-10.pdf',
                 u'foreign_principal': u'Transformation and Continuity, Ajmal Ghani'}],
             u'foreign_principal': u'Transformation and Continuity, Ajmal Ghani',
             u'reg_num': u'5945',
             u'registrant': u'Fenton Communications',
             u'state': None,
             u'url': u'https://efile.fara.gov/pls/apex/f?p=171:200:0::NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:5945,Exhibit%20AB,AFGHANISTAN'}
            ]
        for item in self.items:
            item = json.loads(item)
            assert item in expected
