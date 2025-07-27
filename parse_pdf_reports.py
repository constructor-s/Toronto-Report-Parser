"""
parse_pdf_reports.py
Author: bill.shi (at) mail.utoronto.ca
Date: 2025-07-27

This driver script parses PDF reports using the IOLMasterPDFParser class
from the toronto_report_parser module. It takes a glob pattern as an argument,
searches for matching PDF files, and extracts data from each file. The results
are then flattened and written to an Excel file with each type of parsed result
in a separate sheet.
"""
from toronto_report_parser import IOLMasterPDFParser
import sys
import glob
import pandas as pd

# The first argument is a glob pattern to match PDF files.
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("pattern", help="Glob pattern to match PDF files (e.g., '*.pdf')") # TODO: The shell may expand this automatically, so the Python script may not see the glob pattern as intended.
args = parser.parse_args()

from collections import defaultdict
results = defaultdict(list)  # The key is title
pdf_files = sorted(glob.glob(args.pattern))
for pdf_file in pdf_files:
    with IOLMasterPDFParser(pdf_file) as parser:
        pdf_data = parser.get_pdf_data()
        results[pdf_data["title"]].append(pdf_data)

def flatten_dict(d: dict, parent_key='', sep='_') -> dict:
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
