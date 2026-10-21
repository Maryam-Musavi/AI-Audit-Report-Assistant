import unicodedata
from pypdf import PdfReader 

reader = PdfReader("seo-codal-report.pdf")

page_count: int = len(reader.pages)

print(page_count)

first_page = reader.pages[0]

page_text: str = first_page.extract_text() or ""

page_text = unicodedata.normalize("NFKC", page_text)

print(page_text)

with open("all_pages_layout.txt", mode="w", encoding="utf-8") as file:
    for page_number, page in enumerate(reader.pages, start=1):
        text: str = page.extract_text() or ""

        text = unicodedata.normalize("NFKC", text)

        file.write(f"===== page {page_number} =====\n\n")
        file.write(text)
        file.write("\n\n")

        print(f"Page {page_number} saved")


