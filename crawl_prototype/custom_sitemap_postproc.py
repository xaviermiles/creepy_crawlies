# Pandas is used for convenience, but might need to be replaced with
# base Python functions if/when full_sitemap.csv becomes too large
# (and thus memory/RAM becomes an issue).

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
full_sitemap = pd.read_csv("full_sitemap.csv")
# *** Add custom logic for each column when the columns are more finalised ***
per_website_sitemap = full_sitemap.groupby('website').agg(list)
# Add rows for the non-scraped websites
with open("../results/ccmain-2021-10-nz-netlocs.txt") as f:
    cc_domains = f.read().splitlines()[3:][CC_START:CC_END] # first 3 lines are not URLs
tidy_cc_domains = [f"https://{domain}" for domain in cc_domains]
per_website_sitemap = per_website_sitemap.reindex(per_website_sitemap.index.union(tidy_cc_domains))

per_website_sitemap.to_csv("per_website_sitemap.csv")
print("Finished post-processing")
