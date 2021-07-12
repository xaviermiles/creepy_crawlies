# Scrapy settings for crawl_prototype project
#
# To find more settings:
#   https://docs.scrapy.org/en/latest/topics/settings.html
#   https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#   https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'crawl_prototype'

SPIDER_MODULES = ['crawl_prototype.spiders']
NEWSPIDER_MODULE = 'crawl_prototype.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}
#COOKIES_ENABLED = False  # (enabled by default)
ROBOTSTXT_OBEY = True

# Concurrency
CONCURRENT_REQUESTS = 16  # (default: 16)
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 4

# AutoThrottle extension (disabled by default)
#AUTOTHROTTLE_ENABLED = True
#AUTOTHROTTLE_START_DELAY = 5
#AUTOTHROTTLE_MAX_DELAY = 60
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
#AUTOTHROTTLE_DEBUG = False

# Middlwares, pipelines etc.
#SPIDER_MIDDLEWARES = {
#    'crawl_prototype.middlewares.CrawlPrototypeSpiderMiddleware': 543,
#}
#DOWNLOADER_MIDDLEWARES = {
#    'crawl_prototype.middlewares.CrawlPrototypeDownloaderMiddleware': 543,
#}
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}
#TELNETCONSOLE_ENABLED = False  # (enabled by default)
#ITEM_PIPELINES = {
#    'crawl_prototype.pipelines.CrawlPrototypePipeline': 300,
#}

# HTTP caching (disabled by default)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
