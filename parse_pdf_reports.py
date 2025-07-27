from toronto_report_parser import IOLMasterPDFParser
import sys
import glob
import pandas as pd

# The first argument is a glob pattern to match PDF files.
import argparse
parser = argparse.ArgumentParser(description="Parse PDF reports and export to Excel.")
parser.add_argument("pattern", help="Glob pattern to match PDF files (e.g., '*.pdf')")
args = parser.parse_args()

from collections import defaultdict
results = defaultdict(list)  # The key is title
pdf_files = sorted(glob.glob(args.pattern))
for pdf_file in pdf_files:
    with IOLMasterPDFParser(pdf_file) as parser:
        pdf_data = parser.get_pdf_data()
        results[pdf_data["title"]].append(pdf_data)

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten a nested dictionary."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

# Write each type of parsed result to one sheet in an Excel file.
with pd.ExcelWriter("parsed_results.xlsx") as writer:
    for title, data in results.items():
        df = pd.DataFrame([flatten_dict(d) for d in data])
        df = df.apply(pd.to_numeric, errors='ignore')
        df.to_excel(writer, sheet_name=title[:31], index=False)
