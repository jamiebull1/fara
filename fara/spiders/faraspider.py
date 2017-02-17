# -*- coding: utf-8 -*-
"""Spider for scraping FARA website.
"""
import datetime
from urlparse import unquote, urljoin

from scrapy import FormRequest, Request, Spider, Selector

from fara.items import FaraItem


class FaraSpider(Spider):
    """A spider for crawling the FARA website and retrieving details of agents.
    """
    name = "fara"
    allowed_domains = ["efile.fara.gov"]
    # this start URL is needed to set the cookies initially
    start_urls = [
        "https://efile.fara.gov/pls/apex/f?p=171:130:0::NO:RP,130:P130_DATERANGE:N",
        ]

    def parse(self, response):
        """Fetch all of the results to parse in one shot using the APEX form.
        """
        n_responses = self.settings.get('NUM_RESPONSES', '100000')
        self.logger.info(
            "Running for {n_responses} start rows".format(**locals()))
        form_url = "https://efile.fara.gov/pls/apex/wwv_flow.show"
        apex_params = {
            'p_request': 'APXWGT',
            'p_flow_id': '171',
            'p_flow_step_id': '130',
            'p_widget_num_return': n_responses,  # number of responses per page
            'p_widget_name': 'worksheet',
            'x01': '80340213897823017',
            }
        formrequest = FormRequest(
            form_url,
            formdata=apex_params,
            callback=self.parse_all_principal_agents,
            )
        yield formrequest

    def parse_all_principal_agents(self, response):
        """Parse the full page of foreign principal registrations.
        """
        rows = worksheet_data(response)
        for row in rows:
            yield self.parse_principal_agent(row)

    def parse_principal_agent(self, row):
        """Parse an individual principal agent record.
        """
        item = FaraItem()
        href = row.xpath(
            'td[starts-with(@headers, "LINK BREAK_COUNTRY_NAME")]/a/@href'
            ).extract_first()
        item['url'] = urljoin('https://efile.fara.gov/pls/apex/', href)
        item['country'] = unquote(href.split(',')[-1])
        item['state'] = extract_field(row, 'STATE BREAK_COUNTRY_NAME')
        item['reg_num'] = extract_field(row, 'REG_NUMBER BREAK_COUNTRY_NAME')
        item['address'] = extract_field(row, 'ADDRESS_1 BREAK_COUNTRY_NAME')
        item['foreign_principal'] = extract_field(
            row, 'FP_NAME BREAK_COUNTRY_NAME')
        date = extract_field(row, 'FP_REG_DATE BREAK_COUNTRY_NAME')
        item['date'] = datetime.datetime.strptime(date, "%m/%d/%Y")
        item['registrant'] = extract_field(
            row, 'REGISTRANT_NAME BREAK_COUNTRY_NAME')
        request = Request(
            url=item['url'],  # takes us to the registrant's page for exhibits
            callback=self.parse_exhibits,
            dont_filter=True,  # in case of multiple FPs per registrant
            meta={'item':item})
        return request

    def parse_exhibits(self, response):
        """Extract the PDF url for each exhibit.

        There may be more than one and the response may contain exhibits which
        are not related to the current foreign principal so the logic is a
        little complicated here.

        It seems like the right approach is to fetch all items which are
        related to the current foreign principal and return them as a list.

        Sadly there are formatting inconsistencies, typos, registrations with
        no matching name, etc. that mean the matching isn't 100% accurate.

        Eventually, I feel the best approach is to return a dict item with
        date_stamp, link text, and the url since this gives the best chance
        of disambiguating at a later date.
        """
        item = response.meta.get('item', {})
        rows = worksheet_data(response)
        doclinks = []
        for row in rows:
            foreign_principal = row.xpath(
                'td[@headers="DOCLINK"]/a//text()').extract_first()
            date = extract_field(row, 'DATE_STAMPED')
            date = datetime.datetime.strptime(date, "%m/%d/%Y")
            url = row.xpath('td[@headers="DOCLINK"]/a/@href').extract_first()
            url = urljoin('http://www.fara.gov/docs/', url)
            doclinks.append({'date': date,
                             'foreign_principal': foreign_principal.strip(),
                             'exhibit_url': url})
        # pass doclinks to a no-op stub, where disambiguation can be added
        doclinks = disambiguate_doclinks(item, doclinks)
        item['exhibit_urls'] = doclinks
        yield item


def worksheet_data(response):
    """Get the rows of an APEX worksheet data table.
    """
    table = Selector(response).xpath('//table[@class="apexir_WORKSHEET_DATA"]')
    rows = table.xpath('//tr[@class="odd"]')
    rows.extend(table.xpath('//tr[@class="even"]'))
    return rows


def extract_field(row, header):
    """Extract a specified item from the foreign principal row.
    """
    tag = row.xpath(
        'td[starts-with(@headers, "{header}")]/text()'.format(**locals()))
    text = tag.extract()
    text = '\r\n'.join(line.strip() for line in text)
    return text


def disambiguate_doclinks(item, doclinks):
    """Stub to contain disambiguation logic.

    This might include a fuzzy match between the item['foreign_principal'] and
    the doclink['foreign_principal'], at the risk of losing some relevant
    exhibits.

    A second possibility is matching on the doclink['date'] and item['date'],
    though again this is not a perfect method.
    """
    return doclinks


