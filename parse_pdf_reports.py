from toronto_report_parser import IOLMasterPDFParser
import sys
import glob
# The first argument is a glob pattern to match PDF files.
pdf_files = glob.glob(sys.argv[1])
for pdf_file in pdf_files:
    with IOLMasterPDFParser(pdf_file) as parser:
        pdf_data = parser.get_pdf_data()
        if len(pdf_data) > 20:
            print(pdf_data)
            break
