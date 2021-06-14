# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class CrawlPrototypeItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class LinkItem(Item):
    link = Field()
    text = Field()
    level = Field()  # example.com = 1, example.com/about-us = 2, ...
    has_about_us = Field()
    
    
class GenericWebpageItem(Item):
    url = Field()
    level = Field()
    referer = Field()
    website = Field()
    
    text = Field()
    
    phone_numbers = Field()
    social_links = Field()
    
    test = Field()
    
    
class AboutUsItem(GenericWebpageItem):
    # TODO: add specific fields for AboutUs/ContactUs pages
    pass
    
    
class HomepageItem(GenericWebpageItem):
    # Sufficient to record these fields only once per website/domain
    cart_software = Field()
    has_card = Field()
    payment_systems = Field()
    
    ip_address = Field()
    as_number = Field()
    reverse_dns_lookup = Field()
    