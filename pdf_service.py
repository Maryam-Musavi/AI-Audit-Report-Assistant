"""Persian-safe PDF/Excel text extraction for the audit report.

Why this module exists
----------------------
Persian text coming out of PDFs breaks in four independent ways:

1. Body text: ``pypdf`` glues table cells together and loses reading order.
   PyMuPDF with its default (unsorted) ``get_text("text")`` keeps logical order.
   Do NOT pass ``sort=True``: it scrambles the order for this report.
2. Tables: ``pdfplumber`` returns the letters of every word reversed (visual
   order). ``bidi.get_display`` on each cell restores logical order.
3. Digits: the PDF mixes Arabic-Indic (٣ ٢ ١ ٠ ٨) and Persian (۴ ۵ ۶) digits.
4. Letters: after NFKC the text still contains Arabic ي ك ى and ھ, which
   breaks search/embedding matching against the normal Persian ی ک ه.

``normalize_fa`` fixes 3 and 4 (and presentation forms like ﺷ ﺮ); everything
that leaves this module goes through it.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pdfplumber
import pymupdf
from bidi.algorithm import get_display

_CHAR_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh
        "ى": "ی",  # alef maksura
        "ك": "ک",  # Arabic kaf
        "ھ": "ه",  # heh doachashmee
        "ۀ": "ه",  # heh with yeh above
        "ە": "ه",  # ae
    }
)
# Arabic-Indic digits and Persian digits -> ASCII digits
_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "0123456789" * 2)


def normalize_fa(text: str) -> str:
    """Normalize Persian text: letter forms, Arabic variants and digits."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_CHAR_MAP).translate(_DIGIT_MAP)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def fix_visual_cell(text: str) -> str:
    """Fix a table cell that was extracted in visual (reversed) order."""
    return normalize_fa(get_display(text, base_dir="R"))


def extract_page_text(pdf_path: str | Path, page_index: int) -> str:
    """Return normalized text of one page (0-based index)."""
    with pymupdf.open(str(pdf_path)) as document:
        raw = document[page_index].get_text("text")
    lines = (normalize_fa(line) for line in raw.splitlines())
    return "\n".join(line for line in lines if line)


def extract_all_pages(pdf_path: str | Path) -> list[str]:
    """Return normalized text for every page, in order."""
    with pymupdf.open(str(pdf_path)) as document:
        page_count = len(document)
    return [extract_page_text(pdf_path, i) for i in range(page_count)]


def extract_tables(pdf_path: str | Path, page_index: int) -> list[list[list[str | None]]]:
    """Return all tables on a page with every cell fixed and normalized."""
    fixed_tables: list[list[list[str | None]]] = []
    with pdfplumber.open(str(pdf_path)) as document:
        for table in document.pages[page_index].extract_tables():
            fixed_tables.append(
                [
                    [None if cell is None else fix_visual_cell(cell) for cell in row]
                    for row in table
                ]
            )
    return fixed_tables


def read_codal_excel_tables(xls_path: str | Path):
    """Read the Codal "xls" export (really an HTML file) into DataFrames.

    This is the most reliable source for financial figures because no
    reversing is needed; only normalization (digits, Arabic letters).
    """
    import pandas as pd

    tables = pd.read_html(str(xls_path))
    cleaned = []
    for table in tables:
        table = table.copy()
        table.columns = [
            normalize_fa(" ".join(map(str, c)) if isinstance(c, tuple) else str(c))
            for c in table.columns
        ]
        table = table.map(lambda v: normalize_fa(v) if isinstance(v, str) else v)
        cleaned.append(table)
    return cleaned
