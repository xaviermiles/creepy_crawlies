# Contains WaybackSitemapSpider, which uses the Wayback Machine website
# (https://archive.org/web/) to get information about various websites as they
# were in the past.

# NOTE: I don't know how to cleanly override CustomSitemapSpider (i.e. without
# having to rewrite CustomSitemapSpider).

import re
from datetime import datetime
from scrapy import Request
from scrapy_wayback_machine import UnhandledIgnoreRequest

# local:
from crawl_prototype import items
from crawl_prototype.spiders.custom_sitemap import CustomSitemapSpider


class WaybackSitemapSpider(CustomSitemapSpider):
    name = 'wayback_sitemap'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_wayback_machine.WaybackMachineMiddleware': 543,
        },
        'WAYBACK_MACHINE_TIME_RANGE': ('20200101120000', '20200301120000')
    }

    def get_wayback_meta(self, response, item):
        item['wayback_url'] = response.meta['wayback_machine_url']
        dt_str = re.search("^https://web.archive.org/web/(\d{14})id_/",
                           item['wayback_url']).groups(1)[0]
        item['wayback_dt'] = dt_str
        return item
        
    def parse_homepage(self, response):
        enhanced_item = items.HomepageItem(wayback=True)
        enhanced_item = self.get_wayback_meta(response, enhanced_item)
        return super().parse_homepage(response, enhanced_item)
        
    def parse_about_us(self, response):
        enhanced_item = items.AboutUsItem(wayback=True)
        enhanced_item = self.get_wayback_meta(response, enhanced_item)
        return super().parse_homepage(response, enhanced_item)
    
    def parse(self, response):
        self.logger.info(response.url)
        