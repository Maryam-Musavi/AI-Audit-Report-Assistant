from pdf_service import extract_all_pages

PDF_PATH = "seo-codal-report.pdf"
OUTPUT_PATH = "all_pages.txt"

pages: list[str] = extract_all_pages(PDF_PATH)

print(f"Pages: {len(pages)}")
print(pages[0])

with open(OUTPUT_PATH, mode="w", encoding="utf-8") as file:
    for page_number, text in enumerate(pages, start=1):
        file.write(f"===== page {page_number} =====\n\n")
        file.write(text)
        file.write("\n\n")
        print(f"Page {page_number} saved")
