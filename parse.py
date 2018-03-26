import os
import sys
from _csv import QUOTE_NONNUMERIC
from csv import DictWriter

from PyPDF2 import PdfFileReader


class PdfParser:
    FIELD_ATTRIBUTES = {
        "/FT": "Field Type",
        "/Parent": "Parent",
        "/T": "Field Name",
        "/TU": "Alternate Field Name",
        "/TM": "Mapping Name",
        "/Ff": "Field Flags",
        "/V": "Value",
        "/DV": "Default Value"
    }

    def __init__(self) -> None:
        self._fd = None
        self._pdf = None

        self._headers = []
        self._fields = {}

    def open(self, filename=""):
        if not os.path.isfile(filename) or not os.access(filename, os.R_OK):
            return

        self._fd = open(filename, "rb")
        self._pdf = PdfFileReader(self._fd)

    def extract(self):
        if not self._fd or not self._pdf:
            return

        catalog = self._pdf.trailer["/Root"]
        if "/AcroForm" not in catalog:
            return

        tree = catalog["/AcroForm"]
        if tree is None or "/Fields" not in tree:
            return

        raw_fields = tree["/Fields"]

        for raw_field in raw_fields:
            field_obj = raw_field.getObject()
            field = field_obj.getObject()

            if "/T" in field:
                key = str(field["/T"])

                value = ""
                if "/V" in field:
                    rawvalue = field["/V"]
                    if len(rawvalue) > 0:
                        try:
                            value = float(rawvalue)
                        except ValueError:
                            value = str(rawvalue)

                if key not in self._headers:
                    self._headers.append(key)

                self._fields[key] = value

    def close(self):
        self._fd.close()

    def fields(self):
        return self._fields

    def headers(self):
        return self._headers


if __name__ == "__main__":
    files = sys.argv[1:]

    rows = []

    parser = PdfParser()

    for file in files:
        parser.open(file)
        parser.extract()
        parser.close()
        fields = parser.fields()
        rows.append(fields)

    headers = parser.headers()

    if len(headers) == 0:
        sys.exit(0)

    out_fd = open("output.csv", "w")
    csvwriter = DictWriter(
        out_fd,
        delimiter=",",
        quotechar="\"",
        quoting=QUOTE_NONNUMERIC,
        fieldnames=headers
    )

    csvwriter.writeheader()

    for row in rows:
        csvwriter.writerow(row)

    out_fd.close()
