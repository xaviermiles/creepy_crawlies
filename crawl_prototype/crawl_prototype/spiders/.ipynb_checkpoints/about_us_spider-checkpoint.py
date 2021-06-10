import scrapy
from scrapy.loader import ItemLoader
from crawl_prototype.items import LinkItem

from urllib.parse import urlsplit


class AboutUsSpider(scrapy.Spider):
    name = "about_us"
    
    
    with open("~/web_sentiment_analysis/commoncrawl/digital_economy/results/ccmain-2021-10-nz-netlocs.txt") as f:
        cc_curls = f.read()[3:]
    start_urls = ['https://www.macpac.co.nz/']
    
    def parse(self, response):
        print(response)
        print(cc_urls[:10])
        
        self.logger.info("Engaging spiderman")
        about_us_links = []
        
        links = response.xpath("//a")
        link_item = LinkItem()
        
        for link in links:
            href = link.xpath("@href").get()
            if href is None: 
                continue
                
#             link_item['referral_source'] = 
            link_item['link'] = href
            text = link.xpath("text()").get() or ""
            link_item['text'] = text.strip()
            
            # should work for relative & absolute hrefs???
            link_item['level'] = len(list(filter(None, urlsplit(href).path.split('/')))) + 1
            
            has_about_us = 'about-us' in href or 'about us' in text.lower()
            link_item['has_about_us'] = has_about_us
            if has_about_us:
                about_us_links.append(href)

            yield link_item
    
#         print(about_us_links)
#         for link in about_us_links:
#             pass
        
    def parse_about_us(self, response):
        pass
        