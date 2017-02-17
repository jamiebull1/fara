# -*- coding: utf-8 -*-
"""Pipeline to clean items before export.
"""

class FaraPipeline(object):
    """Simple pipeline to ensure correct formatting.
    """
    def process_item(self, item, spider):
        """Set empty items to None so they become null in json.
        """
        if item['state'] == "":
            item['state'] = None
        if item['address'] == "":
            item['address'] = None
        if not item['exhibit_urls']:
            item['exhibit_urls'] = None
            spider.logger.error(
                 'Failed to retrieve exhibit_urls for {}'.format(item['url']))
        return item
