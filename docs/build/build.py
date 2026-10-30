"""Regenerate the three reports with a table of contents that carries real page numbers.

The page numbers are read back from a LibreOffice PDF render, so the document is built
twice: once to measure, once to fill the contents. A third pass runs only if the
contents page itself changed length and shifted the body.
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import docx_common
import gen_proposal
import gen_report
import gen_sdd
import gen_srs

OUT = pathlib.Path(__file__).parent / "out"
DOCS = [
    (gen_proposal, "IoT_Cat_Feeder_Proposal_V1.0.0.docx"),
    (gen_srs, "IoT_Cat_Feeder_SRS_V1.0.0.docx"),
    (gen_sdd, "IoT_Cat_Feeder_SDD_V1.0.0.docx"),
    (gen_report, "IoT_Cat_Feeder_Report_V1.0.0.docx"),
]


def normalise(text):
    return re.sub(r"\s+", " ", text).strip()


def page_map(docx_path):
    """Return {normalised heading: 1-based page number} from a PDF render."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp,
                        str(docx_path)], check=True, capture_output=True, timeout=300)
        pdf = pathlib.Path(tmp) / (pathlib.Path(docx_path).stem + ".pdf")
        text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                              capture_output=True, text=True).stdout
    found = {}
    for page_number, page in enumerate(text.split("\f"), 1):
        for line in page.splitlines():
            key = normalise(line)
            if key and key not in found:
                found[key] = page_number
    return found


def lookup(headings, found):
    entries = []
    for level, text in headings:
        key = normalise(text)
        page = found.get(key)
        if page is None:
            matches = [p for line, p in sorted(found.items(), key=lambda kv: kv[1])
                       if key and key in line]
            page = matches[0] if matches else 1
        entries.append((level, text, page))
    return entries


def build_one(module, filename, passes=3):
    previous = None
    for attempt in range(1, passes + 1):
        module.build(OUT, toc_entries=previous)
        headings = [(level, text) for level, text in docx_common.HEADINGS if level <= 2]
        found = page_map(OUT / filename)
        entries = lookup(headings, found)
        if entries == previous:
            return filename, attempt
        previous = entries
    module.build(OUT, toc_entries=previous)
    return filename, passes


if __name__ == "__main__":
    if not shutil.which("soffice") or not shutil.which("pdftotext"):
        sys.exit("soffice and pdftotext are required to measure page numbers")
    OUT.mkdir(exist_ok=True)
    for module, filename in DOCS:
        name, rounds = build_one(module, filename)
        print(f"{name}  ({rounds} passes)")
