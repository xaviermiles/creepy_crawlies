# Run using:
# $ cd ~/web_sentiment_analysis/commoncrawl/digital_economy/crawl_prototype
# $ bash run_custom_sitemap.sh

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

import logging
import socket
import urllib3, requests
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import urlsplit

import scrapy
from scrapy import Request
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

# local:
from scrapy.spiders import SitemapSpider
from crawl_prototype.items import GenericWebpageItem, HomepageItem


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
                raise ValueError("cc_start should be < cc_end")
            elif cc_start_int <= 3:
                raise ValueError("cc_start should be >= 4")
            elif cc_end_int > NUM_LINES:
                raise ValueError(f"cc_end should be <= {NUM_LINES} (num_lines)")
        
        with open("../old_reference_material/ccmain-2021-10-nz-netlocs.txt") as f:
            # Subtract one from cc_start/cc_end so that they 
            # correspond to line numbers.
            cc_domains = f.read().splitlines()[(cc_start_int - 1):(cc_end_int - 1)]
        self.logger.info(cc_domains)
        # self.sitemap_urls is normally used but the start_requests method is 
        # adapted to handle this dictionary structure, so parse_homepage and
        # parse_about_us are called together(-ish because of concurrency).
        self.sitemap_urls_dict = {
            f"https://{domain}": get_robots_or_sitemap(domain, self.logger)
            for domain in cc_domains
        }
        self.logger.info(f"Sitemap dictionary:\n{self.sitemap_urls_dict}")
        
        super(CustomSitemapSpider, self).__init__(*a, **kw)

    def start_requests(self):
        for homepage, robots_or_sitemap in self.sitemap_urls_dict.items():
            yield Request(homepage, callback=self.parse_homepage)
            if robots_or_sitemap:
                yield Request(robots_or_sitemap, callback=self._parse_sitemap)
    
    def parse_homepage(self, response):
        hp_item = HomepageItem()
        hp_item['url'] = response.url
        hp_item['level'] = 1
        hp_item['referer'] = None
        hp_item['website'] = get_domain(response.url)
        
        # ADD HOSTING INFORMATION LIKE: ip address, AS number, AS company, reverse DNS lookup etc. etc.
        hp_item['ip_address'] = response.ip_address
#         hp_item['test'] = requests.get(f"http://whois.arin.net/rest/ip/{response.ip_address}").content
        hp_item['test'] = response.ip_address.reverse_pointer
        try:
            hp_item['reverse_dns_lookup'] = socket.gethostbyaddr(str(response.ip_address))[0]
        except socket.herror as e:
            if e.strerror == "Unknown host":
                hp_item['reverse_dns_lookup'] = "Unknown"
            else:
                raise e
        
        yield hp_item
    
    def parse_about_us(self, response):
#         print(dir(response))
        gwp_item = GenericWebpageItem()
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
