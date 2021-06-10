#!/bin/bash
# Limits the number of websites which are used.
CC_START=5000
CC_END=5020

# scrapy outputs a LARGE AMOUNT of logging information; easier to
# navigate with a freshly-clean console.
clear

# ---Three options for logging---------------------------------------
# 1. Just console:
# scrapy crawl custom_sitemap -O full_sitemap.csv \
#   -a cc_start=$CC_START -a cc_end=$CC_END
# -------------------------------------------------------------------
# 2. Both console and txt file:
exec &> >(tee custom_sitemap_log.txt)
scrapy crawl custom_sitemap -O full_sitemap.csv \
  -a cc_start=$CC_START -a cc_end=$CC_END
# -------------------------------------------------------------------
# 3. Just txt file:
# scrapy crawl custom_sitemap -O full_sitemap.csv \
#   --logfile custom_sitemap_log.txt \
#   -a cc_start=$CC_START -a cc_end=$CC_END
# -------------------------------------------------------------------

# Post-processing
python3 custom_sitemap_postproc.py --cc_start $CC_START --cc_end $CC_END

