# Contains CustomSitemapSpider and associated helper functions.

# How the spider handles settings.HTTPCACHE_ENABLED==True:
# - (Scrapy caches all responses)
# - Setting ip_address to "*cache copy*"
# - Setting ssl_certificate to "*cache copy*"
# - Setting protocol to "*cache copy*"

# To download ASN lookup file (to be used with pyasn):
# $ ~/.local/bin/pyasn_util_download.py --latest
# $ ~/.local/bin/pyasn_util_convert.py --single <downloaded_RIB_filename> <ipasn_db_filename>

import re
import logging
import socket
import requests
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import urlsplit

from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import ConnectionRefusedError

# local:
import ecom_utils
from crawl_prototype import items, settings

            
def get_url_level(url):
    return len([x for x in urlsplit(url).path.split('/') if x]) + 1

def get_domain(url):
    # Remove www and protocol to ensure consistency between parse_homepage
    # and parse_about_us.
    # !!! It should be verified that this is the most sensible process 
    #     at some point !!!
    url_parts = urlsplit(url)
    domain = url_parts.netloc.replace('www.', '')
    return domain


class CustomSitemapSpider(SitemapSpider):
    name = 'custom_sitemap'
    # Any URLs which include a given regex string will be parsed by the 
    # corresponding method (order matters).
    sitemap_rules = [
        ('/about-?us', 'parse_about_us'),
        ('/(contact-?us)|(contact)', 'parse_about_us'),
#         ('', 'parse'),
    ]
    # Only sitemap URLs which include the given regex strings will be
    # processed.
    sitemap_follow = ['\.nz/']

    def __init__(self, cc_start=4, cc_end=14, *a, **kw):
        with open("../old_reference_material/ccmain-2021-10-nz-netlocs.txt") as f:
            cc_domains_all = f.read().splitlines()
        try:
            # These arguments are passed from console when initiating scrapy.
            cc_start_int = int(cc_start)
            cc_end_int = int(cc_end)
        except ValueError:
            raise ValueError("cc_start and cc_end must be integers")
        else:
            # If integers, verify whether they give a sensible list slice
            # (does not support negative integers).
            num_lines = len(cc_domains_all) + 1
            if cc_start_int > cc_end_int:
                raise ValueError("cc_start should be <= cc_end")
            elif cc_start_int <= 3:
                raise ValueError("cc_start should be >= 4")
            elif cc_end_int > num_lines:
                raise ValueError(f"cc_end should be <= {num_lines} (num_lines+1)")
        # Subtract one from cc_start/cc_end so that they correspond to line 
        # numbers.
        self.homepage_urls = [
            f"https://{domain}" 
            for domain in cc_domains_all[(cc_start_int - 1):(cc_end_int - 1)]
        ]
        
        SITEMAP_SUFFIXES = [
            "/robots.txt",
            "/sitemap.xml",
        ]
        self.next_sitemap = {
            i: j for i, j in zip(SITEMAP_SUFFIXES[:-1], SITEMAP_SUFFIXES[1:])
        }
        self.next_sitemap['START'] = SITEMAP_SUFFIXES[0]
           
        super().__init__(*a, **kw)

    def start_requests(self):
        for homepage in self.homepage_urls:
            yield Request(homepage, callback=self.parse_homepage)
            
            sitemap_to_try = self.next_sitemap['START']
            yield Request(
                homepage + sitemap_to_try, 
                callback=self._parse_sitemap, 
                errback=self.sitemap_errback, 
                meta={'homepage': homepage, 'sitemap': sitemap_to_try}
            )
           
    def sitemap_errback(self, failure):
        # If the website doesn't have the given sitemap suffix (ie returns 404
        # status code), then the next suffix is tried (if there is a next one).
        if failure.check(HttpError) and failure.value.response.status == 404:
            homepage = failure.request.meta['homepage']
            tried_sitemap = failure.request.meta['sitemap']
            next_sitemap = self.next_sitemap.get(tried_sitemap)
            if next_sitemap:
                yield Request(
                    homepage + next_sitemap, 
                    callback=self._parse_sitemap,
                    errback=self.sitemap_errback,
                    meta={'homepage': homepage, 'sitemap': next_sitemap}
                )
                
        elif failure.check(ConnectionRefusedError):
            pass
            
    def parse_homepage(self, response, preexisting_item=None):
        """
        parse_homepage: FILL OUT
        """
        hp_item = preexisting_item or items.HomepageItem()
        
        # "Content"
        bs = BeautifulSoup(response.body, 'html.parser')
        hp_item['title'] = bs.find('title').get_text()
        author_tag = bs.find('meta', {'name': 'author', 'content': True})
        hp_item['author'] = author_tag['content'] if author_tag else None
        description_tag = bs.find('meta', {'name': 'description', 'content': True})
        hp_item['description'] = description_tag['content'] if description_tag else None
        
        footer = bs.find('footer')
        if footer:
            text_parts = [x for x in re.split(r'\n|\t|\r', footer.get_text()) if x]
            # \xa9 is unicode for the copyright symbol
            text_parts_copyright = [
                re.match(r'^.*(\xa9|copyright).*$', text, flags=re.I)
                for text in text_parts
            ]
            hp_item['copyright'] = [
                t.group(0).strip() for t in text_parts_copyright if t
            ]
        
        # (Try to) Detect ecommerce software
        response_html = response.body.decode()
        hp_item['cart_software'] = ecom_utils.detect_cart_softwares(response_html)
        hp_item['has_card'] = ecom_utils.detect_if_has_card(response_html)
        hp_item['payment_systems'] = ecom_utils.detect_payment_systems(response_html)
        
        # Add more hosting information? e.g. AS number, AS company
        hp_item['ip_address'] = response.ip_address
        hp_item['ssl_certificate'] = (response.certificate is not None
                                      if not settings.HTTPCACHE_ENABLED 
                                      else "*cached copy*")
        hp_item['protocol'] = (response.protocol 
                               if not settings.HTTPCACHE_ENABLED 
                               else "*cached copy*")
        
#         hp_item['test'] = requests.get(f"http://whois.arin.net/rest/ip/{response.ip_address}").content
#         hp_item['test'] = (response.ip_address.reverse_pointer 
#                            if not settings.HTTPCACHE_ENABLED 
#                            else "*cached copy*")
        try:
            hp_item['reverse_dns_lookup'] = (
                socket.gethostbyaddr(str(response.ip_address))[0] 
                if not settings.HTTPCACHE_ENABLED else "*cached copy*"
            )
        except socket.herror as e:
            if e.strerror == "Unknown host":
                hp_item['reverse_dns_lookup'] = "Unknown"
            else:
                raise e
        
        return self.parse_generic_webpage(response, preexisting_item=hp_item)
    
    def parse_about_us(self, response, preexisting_item=None):
        """
        parse_about_us: FILL OUT
        """
        au_item = preexisting_item or items.AboutUsItem()
        # TODO: add specific logic for AboutUs/ContactUs pages
        
        return self.parse_generic_webpage(response, preexisting_item=au_item)
    
    def parse_generic_webpage(self, response, preexisting_item=None):
        """
        parse_generic_webpage: FILL OUT
        """
        gwp_item = preexisting_item or items.GenericWebpageItem()
        
        gwp_item['url'] = response.url
        gwp_item['level'] = get_url_level(response.url)
        referer = response.request.headers.get('referer', None)
        gwp_item['referer'] = referer.decode() if referer else None
        gwp_item['website'] = get_domain(response.url)
        gwp_item['status_code'] = response.status
        
#         gwp_item['html'] = str(response.body)
#         page_text = BeautifulSoup(response.body, 'html.parser').get_text()
#         clean_text = '\n'.join(x for x in page_text.split('\n') if x)  # remove redundant newlines
#         cleaner_text = unicodedata.normalize('NFKD', clean_text)  # remove decoding mistakes
#         gwp_item['text'] = cleaner_text
    
        gwp_item['phone_numbers'] = set()
        gwp_item['social_links'] = set()
        for a_tag in response.xpath('//a[@href]'):
            href = a_tag.xpath('@href').get()
            if href.startswith('tel:'):
                # telephone number is contained within either the href or text
                if len(href) > 4:
                    gwp_item['phone_numbers'].add(href[4:])
                else:
                    gwp_item['phone_numbers'].add(a_tag.xpath('text()').get()) 
            if any(social_name in href for social_name in ['facebook','instagram','twitter','youtube','linkedin']):
                gwp_item['social_links'].add(href)
        
        yield gwp_item
