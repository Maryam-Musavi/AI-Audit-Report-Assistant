"""متن صفحات PDF، رکوردهای صفحه‌ها و قطعه‌های متن را ذخیره می‌کند."""

import json

from backend.paths import GENERATED, PDF_PATH
from backend.services.pdf_service import extract_all_pages
from backend.services.chunk_service import chunk_pages


OUTPUT_PATH = GENERATED / "all_pages.txt"
JSON_PATH = GENERATED / "pages.json"
CHUNKS_PATH = GENERATED / "chunks.json"

pages = extract_all_pages(PDF_PATH)
print(f"Pages: {len(pages)}")
if len(pages) >= 2:
    print("===== Page 2 preview =====")
    print(pages[1])
else:
    print("The PDF has fewer than 2 pages.")

page_records = []

for number, text in enumerate(pages, start=1):
    page_record = {
        "source": PDF_PATH.name,
        "page_number": number,
        "text": text,
    }
    page_records.append(page_record)

print(f"Page records: {len(page_records)}")

with open(OUTPUT_PATH, mode="w", encoding="utf-8") as file:
    for number, text in enumerate(pages, start=1):
        file.write(f"===== page {number} =====\n\n{text}\n\n")

print(f"Saved: {OUTPUT_PATH}")

with open (JSON_PATH, mode="w", encoding="utf-8") as file:
    json.dump(page_records, file, ensure_ascii=False, indent=2)

print(f"Saved: {JSON_PATH}")

with open(JSON_PATH, mode="r", encoding="utf-8") as file:
    saved_pages = json.load(file)

print(f"Loaded pages: {len(saved_pages)}")

if saved_pages:
    first_page = saved_pages[0]
    print(f"Source: {first_page['source']}")
    print(f"Page number: {first_page['page_number']}")
    print(f"Text preview: {first_page['text'][:200]}")


chunks = chunk_pages(page_records)

print(f"Chunks: {len(chunks)}")

with open(CHUNKS_PATH, mode="w", encoding="utf-8") as file:
    json.dump(chunks, file, ensure_ascii=False, indent=2)

print(f"saved: {CHUNKS_PATH}")
