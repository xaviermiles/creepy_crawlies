# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


# For custom_sitemap_spider and wayback_sitemap_spider:
class GenericWebpageItem(Item):
    # Fields recorded from every webpage on a website
    url = Field()
    level = Field()
    referer = Field()
    website = Field()
    status_code = Field()
    
    html = Field()
    text = Field()
    
    phone_numbers = Field()
    social_links = Field()
    
    test = Field()
    
    def __init__(self, wayback=False, *a, **kw):
        if wayback:
            self.fields['wayback_url'] = Field()
            self.fields['wayback_dt'] = Field()
        
        super().__init__(*a, **kw)

    
class AboutUsItem(GenericWebpageItem):
    # TODO: add specific fields for AboutUs/ContactUs pages
    pass
    
    
class HomepageItem(GenericWebpageItem):
    # Fields only recorded from the homepage of each website
    title = Field()
    description = Field()
    author = Field()
    copyright = Field()
    
    cart_software = Field()
    has_card = Field()
    payment_systems = Field()
    
    ip_address = Field()
    ssl_certificate = Field()
    protocol = Field()
    as_number = Field()
    reverse_dns_lookup = Field()
    