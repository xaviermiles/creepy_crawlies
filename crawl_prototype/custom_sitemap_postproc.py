# Pandas is used for convenience, but might need to be replaced with
# base Python functions if full_sitemap.csv becomes too large and 
# memory becomes an issue.

import argparse
import pandas as pd
from collections import OrderedDict

# local:
from crawl_prototype import items


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
def general_agg_func(x):
    x_filt = [y for y in x if y != 'set()']
    x_filt_tidy = list(pd.Series(x_filt, dtype='object')
                       .dropna()
                       .drop_duplicates()
                       )
    return x_filt_tidy


per_website_sitemap = full_sitemap.groupby('website').agg(general_agg_func)
# Add rows for the non-scraped websites (websites that blocked the crawl).
# Subtract one from CC_START/CC_END so that they correspond to line numbers.
with open("../old_reference_material/ccmain-2021-10-nz-netlocs.txt") as f:
    cc_domains = f.read().splitlines()[(CC_START - 1):(CC_END - 1)]
per_website_sitemap = per_website_sitemap.reindex(cc_domains)
# Make line numbers the indices, move websites from index to column
per_website_sitemap = per_website_sitemap.reset_index(level=0)
per_website_sitemap.index = pd.Index(range(CC_START, CC_END), name='txt_line_num')

# Add field groupings
group_to_field = OrderedDict({
    'General': ['website','title','description','author','copyright'],
    'eCommerce': ['cart_software','has_card','payment_systems'],
    'Marketing': ['social_links','phone_numbers'],
    'Hosting': ['ip_address','ssl_certificate','protocol','as_number','reverse_dns_lookup','status_code'],
    'PageDetails': ['url','html','text','level','referer'],
    'Other': ['test']
})
# Check that the fields are the same as the fields in the relevant items
items = [items.GenericWebpageItem(), items.HomepageItem(), items.AboutUsItem()]
actual_fields = set([field for fields in group_to_field.values() 
                     for field in fields])
expected_fields = set([field for item in items 
                       for field in item.fields.keys()])
fields_diff = expected_fields - actual_fields
if len(fields_diff) > 0:
    raise ValueError(f"Not all expected fields included in group_to_fields "
                     f"({', '.join(fields_diff)}).")
# If okay, add to dataframe as MultiIndex
field_to_group = OrderedDict({vi: k for k, v in group_to_field.items() for vi in v})
per_website_sitemap.columns = pd.MultiIndex.from_tuples(
    [(field_to_group[c], c) for c in per_website_sitemap.columns],
    names=['Group','Field']
)


per_website_sitemap.to_csv("custom_sitemap_output/per_website_sitemap.csv")
print("Finished post-processing")

# To import the per-website CSV into Python:
# > pd.read_csv("<filepath>/per_website_sitemap.csv", header=[0,1], index_col=0)
