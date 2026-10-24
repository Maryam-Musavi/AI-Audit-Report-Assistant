"""جدول صفحهٔ ۱۲ PDF را در data/generated/table_page_12.json ذخیره می‌کند."""
import json

from backend.paths import GENERATED, PDF_PATH
from backend.services.pdf_service import extract_tables

PAGE_INDEX = 11  # page 12
OUTPUT_PATH = GENERATED / "table_page_12.json"

tables = extract_tables(PDF_PATH, PAGE_INDEX)
print(f"Tables found: {len(tables)}")

if tables:
    with open(OUTPUT_PATH, mode="w", encoding="utf-8") as file:
        json.dump(tables[0], file, ensure_ascii=False, indent=2)
    print(f"Fixed table saved to {OUTPUT_PATH}")
else:
    print("No table found")
