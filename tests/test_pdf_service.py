import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

from pdf_service import (
    extract_page_text,
    extract_tables,
    fix_visual_cell,
    normalize_fa,
    read_codal_excel_tables,
)

PDF = ROOT / "seo-codal-report.pdf"
XLS = next(ROOT.glob("76b011b7-*.xls"))

BAD_CHARS = re.compile("[يكىھ٠-٩۰-۹]")  # Arabic letter variants + non-ASCII digits


def test_normalize_unifies_digits_and_letters():
    assert normalize_fa("٣,٣۴۶,۵٢٨,۴٣٩") == "3,346,528,439"
    assert normalize_fa("منتھي") == "منتهی"
    assert normalize_fa("ﺷﺮﮐﺖ") == "شرکت"


def test_fix_visual_cell_restores_word_order():
    assert fix_visual_cell("ﻲﺤﻟﺎﺻ ﺪﻤﺣا") == "احمد صالحی"


def test_negative_numbers_keep_parentheses():
    assert fix_visual_cell("(٣۶)") == "(36)"


def test_page_1_text():
    text = extract_page_text(PDF, 0)
    assert "134,341,922" in text
    assert "پالایش نفت بندرعباس" in text
    assert not BAD_CHARS.search(text)


def test_page_21_table_is_logical_order():
    tables = extract_tables(PDF, 20)
    flat = [cell for row in tables[0] for cell in row if cell]
    assert "احمد صالحی" in flat
    assert "0492706387" in flat
    assert "کارشناسی ارشد" in flat
    assert not any(BAD_CHARS.search(c) for c in flat)


def test_excel_income_statement_numbers():
    tables = read_codal_excel_tables(XLS)
    text = "\n".join(t.to_string() for t in tables[:5])
    assert "4,425,065,684" in text
    assert not BAD_CHARS.search(text)
