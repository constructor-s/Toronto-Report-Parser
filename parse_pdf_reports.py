from toronto_report_parser import IOLMasterPDFParser
import sys
import glob
import pandas as pd

# The first argument is a glob pattern to match PDF files.
results = []
pdf_files = glob.glob(sys.argv[1])
for pdf_file in pdf_files:
    with IOLMasterPDFParser(pdf_file) as parser:
        pdf_data = parser.get_pdf_data()
        results.append(pdf_data)

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

df = pd.DataFrame([flatten_dict(data) for data in results])
df.apply(pd.to_numeric, errors='ignore')
df.to_excel("parsed_results.xlsx", index=False)
