import fitz  # PyMuPDF
import warnings
from itertools import groupby

# Create a parser class that uses context manager protocol
class IOLMasterPDFParser:
    def __init__(self, filename):
        self.filename = filename
        self.doc = None

    def __enter__(self):
        self.doc = fitz.open(self.filename)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc is not None:
            self.doc.close()

    def get_pdf_data(self):
        title = self.doc.metadata["title"]
        # if title == "MMT-Full":
        #     warnings.warn("MMT-Full PDF parsing is not implemented yet.")
        if title.startswith("IOL"):
            return self.get_pdf_data_iol()
        elif title == "MMT-Full":
            return self.get_pdf_data_mmt_full()
        else:
            warnings.warn(f"PDF parsing is not implemented yet for {title}.")
            return {}
        
    def get_pdf_data_iol(self):
        result = {
            "filename": self.filename,
            "title": self.doc.metadata["title"]
        }

        page = self.doc[0]
        # Define regions for extracting text
        MIDLINE_X = 0.5 * (313.1999816894531 + 316.0799865722656)
        QUARTER_X = 54.0 + (313.1999816894531 - 54.0) / 2
        if self.doc.metadata["title"] == "IOL-Haigis":
            regions = {
                "region_header_1": (54.0, 56.52001953125, MIDLINE_X, 140.0400390625),
                "region_header_2": (MIDLINE_X, 56.52001953125, 576.0, 140.0400390625),
                "region_od_header": (54.0, 193.79998779296875, 313.1999816894531, 310.6800231933594),
                "region_od_lens_1": (54.0, 310.6800231933594, QUARTER_X, 483.8399963378906),
                "region_od_lens_2": (QUARTER_X, 310.6800231933594, 313.1999816894531, 483.8399963378906),
                "region_od_lens_3": (54.0, 483.8399963378906, QUARTER_X, 657.0),
                "region_od_lens_4": (QUARTER_X, 483.8399963378906, 313.1999816894531, 657.0),
            }
        elif self.doc.metadata["title"] in ("IOL-Holladay-1", "IOL-SRK-T"):
            regions = {
                'region_header_1': (54.0, 56.52001953125, 314.6399841308594, 140.0400390625), 
                'region_header_2': (314.6399841308594, 56.52001953125, 612.0, 140.0400390625), 
                'region_od_header': (54.0, 193.79998779296875, 313.1999816894531, 310.6800231933594), 
                'region_od_lens_1': (54.0, 310.6800231933594, 183.59999084472656, 458.6400146484375), 
                'region_od_lens_2': (183.59999084472656, 310.6800231933594, 313.1999816894531, 458.6400146484375), 
                'region_od_lens_3': (54.0, 458.6400146484375, 183.59999084472656, 606.5999755859375), 
                'region_od_lens_4': (183.59999084472656, 458.6400146484375, 313.1999816894531, 606.5999755859375), 
            }
        else:
            warnings.warn(f"IOL PDF parsing is not implemented yet for {self.doc.metadata['title']}.")
            return result

        for od_name, os_name in [
            ("region_od_header", "region_os_header"),
            ("region_od_lens_1", "region_os_lens_1"),
            ("region_od_lens_2", "region_os_lens_2"),
            ("region_od_lens_3", "region_os_lens_3"),
            ("region_od_lens_4", "region_os_lens_4"),
            ]:
            regions[os_name] = (
                regions[od_name][0] + (316.0799865722656 - 54.0),
                regions[od_name][1],
                regions[od_name][2] + (316.0799865722656 - 54.0),
                regions[od_name][3],
            )

        # Extract text objects for each region
        # text_objects = {key: page.get_text("dict", clip=rect) for key, rect in regions.items()} # This cuts off many text. Also the block bbox is much larger than the span bbox. Some blocks have multiple spans.
        all_text = page.get_text("dict")
        spans = {
            key: self.get_spans_by_origin(all_text["blocks"], rect)
            for key, rect in regions.items()
        }

        result.update(self.get_key_values(spans["region_header_1"]))
        result.update(self.get_key_values(spans["region_header_2"]))
        for eye in ["od", "os"]:
            result[eye] = self.get_key_values(spans[f"region_{eye}_header"])
            result[eye]["lenses"] = {}
            for i in range(1, 5):
                lens = self.get_lens_values(spans[f"region_{eye}_lens_{i}"])
                result[eye]["lenses"][lens["name"]] = lens

        # Store extracted text in a dictionary
        # for key, value in spans.items():
        #     result[key] = self.spans_to_lines(value)

        return result
    
    def get_pdf_data_mmt_full(self):
        result = {
            "filename": self.filename,
            "title": self.doc.metadata["title"]
        }

        page = self.doc[0]

        MIDLINE_X = (54.0 + 576.0) / 2 # 0.5 * (313.1999816894531 + 316.0799865722656)
        regions = {
                "region_header_1": (54.0, 54.0, MIDLINE_X, 135.1199951171875),
                "region_header_2": (MIDLINE_X, 54.0, 576.0, 135.1199951171875),

                "region_od_measurements": (54.0, 259.44000244140625, 313.1999816894531, 653.8800048828125),
                "region_os_measurements": (316.0799865722656, 259.44000244140625, 576.0, 653.8800048828125),
        }

        all_text = page.get_text("dict")
        spans = {
            key: self.get_spans_by_origin(all_text["blocks"], rect)
            for key, rect in regions.items()
        }

        # Remove the spans with the following text in region_od_measurements:
        # to_remove = ('Keratometer values', 'Anterior chamber depth values', 'White-to-white values')
        # spans["region_od_measurements"] = [
        #     span for span in spans["region_od_measurements"]
        #     if span["text"] not in to_remove
        # ]

        result.update(self.get_key_values(spans["region_header_1"]))
        result.update(self.get_key_values(spans["region_header_2"]))
        for eye in ["od", "os"]:
            result[eye] = self.get_mmt_data(spans[f"region_{eye}_measurements"])

        # Store extracted text in a dictionary
        # This is mostly useful for debugging purposes
        for key, value in spans.items():
            result[key] = self.spans_to_lines(value)

        return result

    @staticmethod
    def get_spans_by_origin(all_text_block, rect):
        result = []
        x0, y0, x1, y1 = rect
        # Check if any line in the block overlaps with the region
        for block in all_text_block:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    x, y = span["origin"]
                    if x0 < x < x1 and y0 < y < y1:
                        result.append(span)
        return result
        
    @staticmethod
    def spans_to_lines(spans):
        # Sort the spans by y-coordinate
        # Get the spans into a dictionary with the key being y and the value is a sorted list of (x, y, text) by y-coordinate
        spans = sorted(spans, key=lambda x: x["origin"][1])
        spans_by_y = {}
        # Re-do this but with a slight tolerance for y-coordinate
        prev_y = None
        for span in spans:
            y = span["origin"][1]
            if prev_y is None or abs(y - prev_y) > 1:
                spans_by_y[y] = [span]
                prev_y = y
            else:
                spans_by_y[prev_y].append(span)

        # Sort the spans by x-coordinate within each y group
        for y, v in spans_by_y.items():
            spans_by_y[y] = sorted(v, key=lambda x: x["origin"][0])

        return [[span["text"] for span in spans] for spans in spans_by_y.values()]

    @staticmethod
    def get_key_values(spans):
        # Get the spans into a dictionary with the key being y and the value is a sorted list of (x, y, text) by y-coordinate
        spans_by_y = {}
        for span in spans:
            x, y = span["origin"]
            if y not in spans_by_y:
                spans_by_y[y] = []
            spans_by_y[y].append((x, y, span["text"]))

        results = {}
        # Sort the spans by x-coordinate
        for y, v in spans_by_y.items():
            v = sorted(v, key=lambda x: x[0])

            # Now check if the first item ends with a colon
            # If it does, use it as the key and the next item as the value
            if len(v) > 1 and v[0][2].endswith(":"):
                results[v[0][2][:-1]] = v[1][2]
                
        return results
    
    @staticmethod
    def get_lens_values(spans):
        assert spans, "No spans provided"

        # Sort the spans by y-coordinate
        # Get the spans into a dictionary with the key being y and the value is a sorted list of (x, y, text) by y-coordinate
        spans = sorted(spans, key=lambda x: x["origin"][1])
        spans_by_y = {y: sorted(g, key=lambda s: s["origin"][0]) for y, g in groupby(spans, key=lambda s: s["origin"][1])}

        results = {
            "name": spans_by_y[min(spans_by_y.keys())][0]["text"]
        }
        
        iol_numbers_flag = False
        iol_count = 0
        for y, v in spans_by_y.items():
            # v = sorted(v, key=lambda x: x["origin"][0])
            
            if iol_numbers_flag:
                try:
                    iol = float(v[0]["text"])
                    ref = float(v[1]["text"])
                    results[f"iol_{iol_count}"] = iol
                    results[f"ref_{iol_count}"] = ref
                    iol_count += 1
                    # A bolded line has the following:
                    # {'size': 8.889352798461914, 'flags': 20, 'bidi': 0, 'char_flags': 24, 'font': 'Courier-Bold', 'color': 0, 'alpha': 255, 'ascender': 0.6380000114440918, 'descender': -0.014999999664723873, 'text': '17.5', 'origin': (335.39984130859375, 412.6801452636719), 'bbox': (335.39984130859375, 403.9949951171875, 356.56842041015625, 412.88433837890625)}
                    # A non-bolded line has the following:
                    # {'size': 8.889352798461914, 'flags': 12, 'bidi': 0, 'char_flags': 16, 'font': 'Courier', 'color': 0, 'alpha': 255, 'ascender': 0.6669999957084656, 'descender': -0.12399999797344208, 'text': '17.0', 'origin': (335.39984130859375, 422.400146484375), 'bbox': (335.39984130859375, 414.9043273925781, 357.6484680175781, 423.7936706542969)}
                    # So we will use the flags to determine if the line is bolded or not.
                    if v[0]["flags"] == 20:
                        results[f"iolbold"] = iol
                        results[f"refbold"] = ref
                except (ValueError, IndexError):
                    iol_numbers_flag = False

            # Check if the line 'IOL (D)', 'REF (D)' has reached
            if len(v) >= 2 and v[0]["text"] == "IOL (D)" and v[1]["text"] == "REF (D)":
                iol_numbers_flag = True

            # Now check if the first item ends with a colon
            # If it does, use it as the key and the next item as the value
            if v and v[0]["text"].endswith(":"):
                results[v[0]["text"][:-1]] = v[1]["text"]
            elif v: # e.g. 'Emme. IOL: 21.34'
                parts = v[0]["text"].split(": ", 1)
                if len(parts) == 2:
                    results[parts[0]] = parts[1]
                
        return results

    @staticmethod
    def get_mmt_data(spans):
        result = {}

        # Sort the spans by y-coordinate
        # Get the spans into a dictionary with the key being y and the value is a sorted list of (x, y, text) by y-coordinate
        spans = sorted(spans, key=lambda x: x["origin"][1])
        spans_by_y = {}
        # Re-do this but with a slight tolerance for y-coordinate
        prev_y = None
        for span in spans:
            y = span["origin"][1]
            if prev_y is None or abs(y - prev_y) > 1:
                spans_by_y[y] = [span]
                prev_y = y
            else:
                spans_by_y[prev_y].append(span)
        
        # Next, go through all the text.
        # The format can be:
        # key: value
        # key : value
        # key1:value1 key2:value2
        # key = value
        def get_next_key_value(text):
            i = 0
            
            key_start = 0
            key_end = key_start
            while key_end < len(text) and text[key_end] not in ":=":
                key_end += 1
            
            if key_end == len(text):
                return None, None, ""
            
            value_start = key_end + 1
            value_end = value_start
            while value_end < len(text) and text[value_end] not in ":=":
                value_end += 1
            if value_end < len(text) and text[value_end] in ":=":
                # The scenario is key1:value1 key2:value2
                # Need to back track to the last non-space character
                while value_end > value_start and text[value_end - 1] != " ":
                    value_end -= 1

            return (
                text[key_start:key_end],
                text[value_start:value_end],
                text[value_end:]
            )
        
        for y, v in spans_by_y.items():
            v.sort(key=lambda x: x["origin"][0])  # Sort by x-coordinate

        al_snr_flag = False
        al_snr_count = 0
        acd_flag = False
        for y, v in spans_by_y.items():
            for i, span in enumerate(v):
                text = span["text"]
                while text:
                    key, value, text = get_next_key_value(text)
                    if key or value:
                        if key == "K" and i >= 1 and v[i-1]["text"] == "∆":
                            key = "DeltaK"
                        if key in ("K1", "K2", "DeltaK"):
                            i = 0
                            while f"{key}_{i}" in result:
                                i += 1
                            key = f"{key}_{i}"
                        result[key.strip(" ()")] = value.strip(" ()")
            
            if acd_flag:
                for i in range(len(v)):
                    result[f"ACD_{i}"] = v[i]["text"]
                acd_flag = False
            elif v:
                acd_flag = v[0]["text"].startswith("ACD:")

            # Find the line that starts with "AL" and "SNR"
            # And then record the values on the subsequent lines
            if v and v[0]["text"] == "AL" and v[1]["text"] == "SNR":
                al_snr_flag = True
            elif al_snr_flag:
                # Parse the format: '22.50 mm', '9.7'
                # Techinically it seems there could be another two values in the right column, but I haven't encountered such a report
                try:
                    al = v[0]["text"]
                    al = float(al.replace(" mm", ""))
                    snr = float(v[1]["text"])
                    result[f"AL_{al_snr_count}"] = al
                    result[f"SNR_{al_snr_count}"] = snr
                    al_snr_count += 1
                except (ValueError, IndexError):
                    al_snr_flag = False
        
        return result
                
