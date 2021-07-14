#!/bin/bash
# Limits the number of websites which are used. Refers to the line
# numbers in old_reference_material/ccmain-2021-10-nz-netlocs.txt,
# where these are inclusive lower bound + exclusive upper bound (due
# to Python slicing).
# NOTE: first 3 lines of txt file are not URLs (so CC_START>=4).
CC_START=5000
CC_END=5020
OUTPUT_FOLDER="spiders_output/custom_sitemap"
if [ ! -d $OUTPUT_FOLDER ] 
then
  mkdir $OUTPUT_FOLDER
fi

# scrapy outputs a LARGE AMOUNT of logging information; easier to
# navigate with a freshly-clean console.
clear

# ---Three options for logging---------------------------------------
# 1. Just console:
# scrapy crawl custom_sitemap \
#   -O $OUTPUT_FOLDER/full_sitemap.csv \
#   -a cc_start=$CC_START -a cc_end=$CC_END
# -------------------------------------------------------------------
# 2. Both console and txt file:
exec &> >(tee $OUTPUT_FOLDER/log.txt)
scrapy crawl custom_sitemap \
  -O $OUTPUT_FOLDER/full_sitemap.csv \
  -a cc_start=$CC_START -a cc_end=$CC_END
# -------------------------------------------------------------------
# 3. Just txt file:
# scrapy crawl custom_sitemap \
#   -O $OUTPUT_FOLDER/full_sitemap.csv \
#   --logfile $OUTPUT_FOLDER/log.txt \
#   -a cc_start=$CC_START -a cc_end=$CC_END
# -------------------------------------------------------------------

# Post-processing
python3 custom_sitemap_postproc.py \
  --cc_start $CC_START --cc_end $CC_END --output_folder $OUTPUT_FOLDER
