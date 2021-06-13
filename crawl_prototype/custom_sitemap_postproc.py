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
# !!! Add custom logic for each column when the columns are more finalised !!!
per_website_sitemap = full_sitemap.groupby('website').agg(list)
# Make line numbers the indices, move websites from index to column
per_website_sitemap = per_website_sitemap.reset_index(level=0)
per_website_sitemap.index = pd.Index(range(CC_START, CC_END - 1), name='txt_line_num')

per_website_sitemap.to_csv("custom_sitemap_output/per_website_sitemap.csv")
print("Finished post-processing")
