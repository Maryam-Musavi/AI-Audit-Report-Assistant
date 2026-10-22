import unicodedata
import pdfplumber
import json

from bidi.algorithm import get_display

def fix_visual_cell(text: str) -> str:
    """Fix a table cell extracted in visual order."""

    fixed_text: str = get_display(text, base_dir="R")

    fixed_text = unicodedata.normalize("NFKC", fixed_text)

    return fixed_text

with pdfplumber.open("seo-codal-report.pdf") as document:
    page = document.pages[20]

    tables = page.extract_tables()

    print(f"Tables found: {len(tables)}")

    if tables:
        first_table = tables[0]
        fixed_table: list = []

        for row in first_table:
            fixed_row: list = []

            for cell in row:
                if cell is None:
                    fixed_row.append(None)
                else:
                    fixed_cell: str =fix_visual_cell(text=cell)
                    fixed_row.append(fixed_cell)

            fixed_table.append(fixed_row)
        
        with open(
            "table_page_21.json", 
            mode="w", 
            encoding="utf-8",
        ) as file:
            json.dump(first_table, file, ensure_ascii=False, indent=2)

        
        print("Table saved to table_page_21_fixed.json")
    else:
        print("No table found")