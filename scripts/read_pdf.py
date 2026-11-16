"""متن همهٔ صفحه‌های PDF را در data/generated/all_pages.txt ذخیره می‌کند."""
from backend.paths import GENERATED, PDF_PATH
from backend.services.pdf_service import extract_all_pages

OUTPUT_PATH = GENERATED / "all_pages.txt"

pages = extract_all_pages(PDF_PATH)
print(f"Pages: {len(pages)}")
if len(pages) >= 2:
    print("===== Page 2 preview =====")
    print(pages[1])

    page_record = {
        "source": PDF_PATH.name,
        "page_number": 2,
        "text": pages[1],
    }

    print(page_record["source"], page_record["page_number"])
else:
    print("The PDF has fewer than 2 pages.")

with open(OUTPUT_PATH, mode="w", encoding="utf-8") as file:
    page_records = []

    for number, text in enumerate(pages, start=1):
        page_record = {
            "source": PDF_PATH.name,
            "page_number": number,
            "text": text,
        }
        page_records.append(page_record)

    print(f"Page records: {len(page_records)}")


    for number, text in enumerate(pages, start=1):
        file.write(f"===== page {number} =====\n\n{text}\n\n")

print(f"Saved: {OUTPUT_PATH}")
