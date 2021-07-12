# Contains CustomSitemapSpider and associated helper functions.

# How the spider handles settings.HTTPCACHE_ENABLED==True:
# - Setting ip_address to "*cache copy*"
# - Setting ssl_certificate to "*cache copy*"
# - Setting protocol to "*cache copy*"
# - Keeping a list of robots/sitemaps in txt file, so these HEAD requests do 
#   not need to be sent. Only one cached copy is saved, so the HEAD requests 
#   will be necessary if the saved copy does not have the correct line numbers.

# To download ASN lookup file (to be used with pyasn):
# $ ~/.local/bin/pyasn_util_download.py --latest
# $ ~/.local/bin/pyasn_util_convert.py --single <downloaded_RIB_filename> <ipasn_db_filename>

import re
import os, glob
import json
import logging
import socket
import urllib3, requests
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import urlsplit

import scrapy
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

# local:
import ecom_utils
from crawl_prototype import items, settings


# To silently allow verify=False in requests:
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def does_url_exist(url, logger):
    status_code = get_http_status_code(url, logger)
    if status_code:
        return status_code < 400
            
def get_url_level(url):
    return len(list(filter(None, urlsplit(url).path.split('/')))) + 1

def get_domain(url):
    # Remove www and protocol to ensure consistency between parse_homepage
    # and parse_about_us.
    # !!! It should be verified that this is the most sensible process 
    #     at some point !!!
    url_parts = urlsplit(url)
    return url_parts.netloc.replace('www.', '')
        
    
def get_http_status_code(url, logger):
    try:
        # verify=False is only acceptable since it is a one-time
        # request (ie. no back-and-forth between client & server).
        # Is there a safer alternative???
        # See https://stackoverflow.com/questions/10667960/python-requests-throwing-sslerror
        r = requests.head(url, verify=False)  
        return r.status_code
    except Exception as e:
        logger.info(f"{type(e).__name__}: {url}")
        
        
def get_robots_or_sitemap(domain, logger):
    # Order matters:
    attempts = [
        f"https://{domain}/robots.txt",
        f"https://{domain}/sitemap.xml",
    ]
    
    for url in attempts:
        if does_url_exist(url, logger):
            return url


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
        NUM_LINES = 41170
        try:
            # These arguments are passed from console when initiating scrapy.
            cc_start_int = int(cc_start)
            cc_end_int = int(cc_end)
        except ValueError:
            raise ValueError("cc_start and cc_end must be integers")
        else:
            # If integers, verify whether they give a sensible list slice
            # (does not support negative integers).
            if cc_start_int >= cc_end_int:
                raise ValueError("cc_start should be < cc_end")
            elif cc_start_int <= 3:
                raise ValueError("cc_start should be >= 4")
            elif cc_end_int > NUM_LINES:
                raise ValueError(f"cc_end should be <= {NUM_LINES} (num_lines)")
        
        with open("../old_reference_material/ccmain-2021-10-nz-netlocs.txt") as f:
            # Subtract one from cc_start/cc_end so that they correspond to line
            # numbers.
            cc_domains = f.read().splitlines()[(cc_start_int - 1):(cc_end_int - 1)]
        
        # self.sitemap_urls is normally used but the start_requests method is 
        # adapted to handle this dictionary structure, so parse_homepage and
        # parse_about_us are called together(-ish because of concurrency).
        glob_str = os.path.join("custom_sitemap_output", "cached_sitemaps_*_to_*.json")
        regex_str = "cached_sitemaps_(\d+)_to_(\d+).json"
        glob_match = glob.glob(glob_str)
        line_nums_correct = False
        if glob_match:
            json_fpath = glob.glob(glob_str)[0]  # should only be one match
            line_nums = re.search(regex_str, json_fpath).groups()
            if cc_start_int == int(line_nums[0]) and cc_end_int == int(line_nums[1]):
                line_nums_correct = True
            else:
                self.logger.info("Removing old sitemap_urls_dict JSON file")
                os.remove(json_fpath)  # so there is only one cached file
            
        if settings.HTTPCACHE_ENABLED and line_nums_correct:
            self.logger.info("Loading sitemap_urls_dict from JSON file")
            with open(json_fpath, 'r') as f:
                self.sitemap_urls_dict = json.load(f)
        else:
            self.logger.info("Constructing sitemap_urls_dict and saving to JSON file")
            self.sitemap_urls_dict = {
                f"https://{domain}": get_robots_or_sitemap(domain, self.logger)
                for domain in cc_domains
            }
            json_fpath = os.path.join("custom_sitemap_output", 
                                      f"cached_sitemaps_{cc_start_int}_to_{cc_end_int}.json")
            with open(json_fpath, 'w') as f:
                json.dump(self.sitemap_urls_dict, f)
                
        self.logger.info(f"Sitemap dictionary:\n{self.sitemap_urls_dict}")
        
        super().__init__(*a, **kw)

    def start_requests(self):
        for homepage, robots_or_sitemap in self.sitemap_urls_dict.items():
            yield Request(homepage, callback=self.parse_homepage)
            if robots_or_sitemap:
                yield Request(robots_or_sitemap, callback=self._parse_sitemap)
    
    def parse_homepage(self, response, preexisting_item=None):
        """
        parse_homepage: FILL OUT
        """
        hp_item = preexisting_item or items.HomepageItem()
        self.logger.info(hp_item)
        
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