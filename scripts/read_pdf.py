"""متن همهٔ صفحه‌های PDF را در data/generated/all_pages.txt ذخیره می‌کند."""
from backend.paths import GENERATED, PDF_PATH
from backend.services.pdf_service import extract_all_pages

OUTPUT_PATH = GENERATED / "all_pages.txt"

pages = extract_all_pages(PDF_PATH)
print(f"Pages: {len(pages)}")

with open(OUTPUT_PATH, mode="w", encoding="utf-8") as file:
    for number, text in enumerate(pages, start=1):
        file.write(f"===== page {number} =====\n\n{text}\n\n")

print(f"Saved: {OUTPUT_PATH}")
