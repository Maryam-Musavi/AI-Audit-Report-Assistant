import json

from pdf_service import extract_tables

PDF_PATH = "seo-codal-report.pdf"
PAGE_INDEX = 11  # page 12
OUTPUT_PATH = "table_page_12.json"

tables = extract_tables(PDF_PATH, PAGE_INDEX)

print(f"Tables found: {len(tables)}")

if tables:
    with open(OUTPUT_PATH, mode="w", encoding="utf-8") as file:
        json.dump(tables[0], file, ensure_ascii=False, indent=2)

    print(f"Fixed table saved to {OUTPUT_PATH}")
else:
    print("No table found")
