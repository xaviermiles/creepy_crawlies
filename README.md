# Scraping and Crawling

## Crawling - Inital Outlay
There is a wide variety of web-crawls/crawlers, but they can be grouped into two broad types:
- broad crawls - wanting crawlers to gather information from a (large) group of websites with the crawler *naturally* traversing the internet, which allows for switching between websites if they are linked together (domain-agnostic).
- focussed crawls - wanting crawlers to gather specific information and these will tend to be constrained to given domains (or even URLs).

This project will perform focussed crawls from a specified list of websites to gather specific information that pertains to whether these websites can be linked to a New Zealand business, have any shopping cart software, etc. However, this will be on a LARGE number of websites so the crawlers will have to be fairly general in the way that they approach websites (e.g. will have to be intelligent when looking for an "About Us" section, since websites will have different subdomain-URL structures).

There is four main considerations when setting up (or maintaining) web-crawlers:
- selection policy - which pages to download. We will use a list of websites to start the crawlers, but this crawling will involve searching for links on the main page of the websites, and following these links to other parts of the website (subdomain). Since not every page on a website will contain useful information, selection criterion should be used to tell/inform the crawlers which pages on a website are worth downloading and processing. The traditional way to do this is using importance metrics (e.g. PageRank, On-line Page Importance Computation), which use the number of inbound/outbound links to/from other webpages. For this project, it may be appropriate to explicitly state which types of webpages we are looking for, such as "About Us" or "Contact Us" pages. Both approaches could be used together.
- revisit policy - how often to revisit websites to collect information. This might be set by others in Stats NZ to guarantee consistency in data collection (eg. quarterly or monthly), but this will also be related to computational resources. Subsequent crawls may not need to revisit as much of websites if nothing has changed. For example, changes to a website, and subsequently whether their link to a NZ business and/or digital industry classification may have changed, can be detected by consulting a website's sitemap if the sitemap is in xml format (which is typical) and includes "last modified" tags (e.g. www.macpac.co.nz/sitemap_0.xml).
- politeness policy - how to avoid overloading websites. This is a purely technical decision. This is usually informed by consulting the robots policy on website (e.g. www.macpac.co.nz/robots.txt), but could also be made based on the apparent speed of the website's server.
- parallelisation policy - how to coordinate distributed web crawlers. This will be informed by the crawling framework/technology used.

Very good resource for general info on web crawlers: [not-wikipedia](https://en.wikipedia.org/wiki/Web_crawler).

## Software to use
Currently the crawler(s) have been using the Scrapy package in Python, since this seemed like the most approachable software that still provided a very comprehensive crawling framework. The greatest downside to Scrapy is that it does not provide _"any built-in facility for running crawls in a distribute (multi-server) manner"_, although this can be overcome through manual implementation ([related section in docs](https://docs.scrapy.org/en/latest/topics/practices.html#distributed-crawls)). For example, the list of websites to crawl could be split into partitions and each of these partitions be handled by an identical spider running on a different EC2-instance.
Alternative choices:
- rvest (R)
- Apache Nutch (Java)
- Multiple Python (or R) libraries to create a collection of crawlers distributed across 20 EC2 instances with manually-implemented scraping/crawling framework ([see this guide](https://michaelnielsen.org/ddi/how-to-crawl-a-quarter-billion-webpages-in-40-hours/)). This would provide the most customised option but would be an extreme technical challenge. (Note, the techniques used by the above guide are likely outdated since it is from 2012.)

### Useful sections from Scrapy docs
- [Avoiding getting banned](https://docs.scrapy.org/en/latest/topics/practices.html#avoiding-getting-banned)
- [Dynamic content](https://docs.scrapy.org/en/latest/topics/dynamic-content.html) - either use Splash to pre-render javascript or Selenium (headless browser) to live-render javascript
- [Autothrottling](https://docs.scrapy.org/en/latest/topics/autothrottle.html)
- [General Scrapy architecture](https://docs.scrapy.org/en/latest/topics/architecture.html)
- (Other) [Linking Scrapy to MongoDB](https://realpython.com/web-scraping-with-scrapy-and-mongodb/)
- (Other) [Assorted tips](https://www.zyte.com/blog/scrapy-tips-from-the-pros-part-1/)

### Polite vs effective
There seems to be at least some trade-off between being polite to websites ([related](https://www.zyte.com/blog/how-to-crawl-the-web-politely-with-scrapy/)) and effectively managing to gather information from a website. For example, should the User-Agent correctly identify the bot or use one corresponding to a normal browser?

[Here](https://www.programmersought.com/article/66717873784/) is some tips to get around some measures employed by websites to prevent bots from scraping them.

## Implemented
### custom_sitemap
The aim of this spider is to visit a list of NZ URLs and fetch information from these websites that would help to link these websites to the NZ business register. It was designed to replicate the dataset in Appendix A of [this paper](https://www.cbs.nl/-/media/_pdf/2016/40/measuring-the-internet-economy.pdf) as much as possible.
In the future, it would also be useful if the scraped information could help to inform a _"digital industry"_ classification for the associated businesses and/or provide some idea of how many sales the business makes online.

The current list of URLs is the ".nz" websites included in the February 2021 commoncrawl dataset ([CC-MAIN-2021-10](https://commoncrawl.org/2021/03/february-march-2021-crawl-archive-now-available/)). Unfortunately, this only includes about 40,000 out of an estimated 725,000 NZ websites ([source](https://docs.internetnz.nz/reports/)); a more-complete source of URLs would provide a more-complete scrape of the _New Zealand_ internet. It seems that [internetnz](https://docs.internetnz.nz/) should be able to provide a complete list of ".nz" URLs, since they _"keep the definitive register of .nz domain names"_, although it does not seem like this could be done with any of their current products/APIs.

This spider is a customisation (child class) of Scrapy's SitemapSpider. Most websites have a sitemap that has all the pages on the website, so this provides an easy way to filter the pages (using regex on the URLs) and only visit the pages that are likely to provide useful information. This spider currently only visits the homepage, about us, and contact us pages of each website, and is structured such that each type of page is handled by both custom and generic logic. For example, information will be scraped from the homepage of each website using two functions; *parse_homepage* and *parse_generic_webpage*. This flexible structure means that different fields/information can be collected from only certain types of webpages (or every webpage).

To run this spider, set the console's working directory to `crawl_prototype/` and then run `bash run_custom_sitemap.sh`. This spider:
- is set to run through only 20 websites. To change this, change the values of CC_START & CC_END in `crawl_prototype/run_custom_sitemap.sh`.
- is not set to cache responses, but does allow this option. To change this, set "HTTPCACHE_ENABLED = True" in `crawl_prototype/crawl_prototype/settings.py`.
- is not set to make concurrent requests, since this makes debugging easier. To change this, set CONCURRENT_REQUESTS to some integer greater than 1 in `crawl_prototype/crawl_prototype/settings.py`. If this is changed, the CONCURRENT_REQUESTS_PER_DOMAIN should also be set to a single-digit integer for politeness to servers.
- does not order the columns in the output CSV (TODO - could do in postprocessing python script). There is groupings of the output fields which is also not captured/implied in the output CSV.
- is a work in progress. To try scraping a new piece of information from a webpage response, assign it to the "test" field and it will show up in the output CSV.

Possible improvements:
- Improve scrape success rate by adding javascript/browser support (i.e. Selenium). *Where appropriate*, this would enable circumventing measures used to prevent scraping. [link](https://stackoverflow.com/questions/47315699/scrapy-user-agent-and-robotstxt-obey-are-properly-set-but-i-still-get-error-40)
- Detect HTML version (difficult?). [link](https://howtocheckversion.com/check-html-version-website/)
- Detect Autonomous System Number (ASN) and ASN owner. [link1](https://www.cidr-report.org/as2.0/autnums.html), [link2](https://github.com/hadiasghari/pyasn)

### wayback (TODO)
The aim of this spider is to use the wayback machine (and other web archives?) to provide a back series of the websites scraped by the custom_sitemap spider.

This could be as simple as determining when the business first started using a website, as this would imply when the business _"joined the digital economy"_, which could then be used to derive statistics about the growth of the digital economy over time. However, growth statistics *should* also depend on the amount of revenue derived from the website (directly or otherwise); if this information proves to difficult to gather then a tool like [BuiltWith](https://builtwith.com/) could be used.

The first attempt was the wayback_sitemap spider, which inherits the logic from the custom_sitemap spider and applies a downloader middleware (from *scrapy-wayback-machine* package) to redirect requests to the appropriate URL on the Wayback Machine website. 
This downloader middleware seems to achieve the redirection as expected. It should be verified whether the "sitemap approach" applies alright to the Wayback Machine website, considering that it might not scrape sitemaps very often. 

An alternative wayback spider would use the same downloader middleware but simply requests the homepage, and then use links on each webpage to navigate the (snapshot of the) website to other webpages.
