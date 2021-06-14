# To download ASN lookup file (to be used with pyasn):
# $ ~/.local/bin/pyasn_util_download.py --latest
# $ ~/.local/bin/pyasn_util_convert.py --single <downloaded_RIB_filename> <ipasn_db_filename>

# Additional ideas:
# > Improve scrape success rate by adding javascript/browser support: 
#   - https://stackoverflow.com/questions/47315699/scrapy-user-agent-and-robotstxt-obey-are-properly-set-but-i-still-get-error-40
# > Detect HTML version (difficult?): 
#   - https://howtocheckversion.com/check-html-version-website/
# > Detect AS number (& ASN owner): 
#   - https://www.cidr-report.org/as2.0/autnums.html
#   - https://github.com/hadiasghari/pyasn

# To handle settings.HTTPCACHE_ENABLED==True:
# - Setting ip_address to "*cache copy*"
# - Keeping a list of robots/sitemaps in txt file, so these HEAD requests do 
#   not need to be sent. Only one cached copy is saved, so it will the HEAD
#   requests will be necessary if the saved copy does not have the correct 
#   line numbers.

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
            if cc_start_int >= cc_end_int:
                raise ValueError("cc_start should be less than cc_end")
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
        glob_str = "cached_sitemaps_*_to_*.json"
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
            with open(f"cached_sitemaps_{cc_start_int}_to_{cc_end_int}.json", 'w') as f:
                json.dump(self.sitemap_urls_dict, f)
                
        self.logger.info(f"Sitemap dictionary:\n{self.sitemap_urls_dict}")
        
        super(CustomSitemapSpider, self).__init__(*a, **kw)

    def start_requests(self):
        for homepage, robots_or_sitemap in self.sitemap_urls_dict.items():
            yield Request(homepage, callback=self.parse_homepage)
            if robots_or_sitemap:
                yield Request(robots_or_sitemap, callback=self._parse_sitemap)
    
    def parse_homepage(self, response):
        """
        parse_homepage: FILL OUT
        """
        hp_item = items.HomepageItem()
        
        # (Try to) Detect ecommerce software
        response_html = str(response.body)
        hp_item['cart_software'] = ecom_utils.detect_cart_softwares(response_html)
        hp_item['has_card'] = ecom_utils.detect_if_has_card(response_html)
        hp_item['payment_systems'] = ecom_utils.detect_payment_systems(response_html)
        
        # ADD HOSTING INFORMATION LIKE: ip address, AS number, AS company, reverse DNS lookup etc. etc.
        hp_item['ip_address'] = response.ip_address
#         hp_item['test'] = requests.get(f"http://whois.arin.net/rest/ip/{response.ip_address}").content
        hp_item['test'] = (
            response.ip_address.reverse_pointer 
            if not settings.HTTPCACHE_ENABLED else "*cached copy*"
        )
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
    
    def parse_about_us(self, response):
        """
        parse_about_us: FILL OUT
        """
        au_item = items.AboutUsItem()
        # TODO: add specific logic for AboutUs/ContactUs pages
        
        return self.parse_generic_webpage(response, preexisting_item=au_item)
    
    def parse_generic_webpage(self, response, preexisting_item=None):
        """
        parse_generic_webpage: FILL OUT
        """
        if preexisting_item:
            gwp_item = preexisting_item
        else:
            gwp_item = items.GenericWebpageItem()
        
        gwp_item['url'] = response.url
        gwp_item['level'] = get_url_level(response.url)
        referer = response.request.headers.get('referer', None)
        gwp_item['referer'] = referer.decode() if referer else None
        gwp_item['website'] = get_domain(response.url)
        
        page_text = BeautifulSoup(response.body, 'html.parser').get_text()
        clean_text = '\n'.join(x for x in page_text.split('\n') if x)  # remove redundant newlines
        cleaner_text = unicodedata.normalize('NFKD', clean_text)  # remove decoding mistakes
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
            if any(social_name in href for social_name in ['facebook','instagram','twitter','youtube']):
                gwp_item['social_links'].add(href)
        
        yield gwp_item
