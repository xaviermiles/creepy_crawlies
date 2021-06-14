# Pandas is used for convenience, but might need to be replaced with
# base Python functions if full_sitemap.csv becomes too large and 
# memory becomes an issue.

import argparse
import pandas as pd

# Translate command line arguments into Python variables
parser = argparse.ArgumentParser()
parser.add_argument("--cc_start", type=int)
parser.add_argument("--cc_end", type=int)
args = parser.parse_args()
CC_START, CC_END = args.cc_start, args.cc_end

print("\n\nStarting post-processing")
      
print("...Aggregating output by website...")
full_sitemap = pd.read_csv("custom_sitemap_output/full_sitemap.csv")
# !!! Add custom logic for each column once the columns are more finalised !!!
per_website_sitemap = full_sitemap.groupby('website') \
                                  .agg(lambda x: list(pd.Series(x).dropna()))
# Add rows for the non-scraped websites (websites that blocked the crawl).
# Subtract one from CC_START/CC_END so that they correspond to line numbers.
with open("../old_reference_material/ccmain-2021-10-nz-netlocs.txt") as f:
    cc_domains = f.read().splitlines()[(CC_START - 1):(CC_END - 1)]
per_website_sitemap = per_website_sitemap.reindex(per_website_sitemap.index.union(cc_domains))
# Make line numbers the indices, move websites from index to column
per_website_sitemap = per_website_sitemap.reset_index(level=0)
per_website_sitemap.index = pd.Index(range(CC_START, CC_END), name='txt_line_num')

per_website_sitemap.to_csv("custom_sitemap_output/per_website_sitemap.csv")
print("Finished post-processing")
